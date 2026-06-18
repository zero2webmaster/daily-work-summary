#!/usr/bin/env python3
"""
Portfolio stats generator — monthly LoC + doc-line snapshot of every Z2W repo.

Fulfills the no-urgency bulletin ask from `z2w-agent-command-center` (filed
2026-06-12, amended 2026-06-17): produce a machine-readable, versioned artifact
the phone-first command center (agents.z2w.us) can read via the GitHub Contents
API and render in a portfolio stats panel.

WHERE THE ARTIFACT GOES
-----------------------
The JSON is committed into the `zero2webmaster/z2w-agent-coordination` repo at
`stats/portfolio-YYYY-MM.json`, **NOT** into this (daily-work-summary) repo. The
command center's GitHub token is fine-grained and scoped to the coordination
repo only, so it cannot read an artifact that lives anywhere else (2026-06-17
amendment). The workflow handles the clone + commit of that repo; THIS script
just computes the stats and writes the JSON to a path it is given.

DESIGN
------
- Self-contained (does not import generate_summary.py) so the monthly stats job
  is fully decoupled from the nightly email job — nothing here can ever affect
  Kerry's morning digest.
- Per-repo work is exception-wrapped: one repo that fails to clone or measure is
  recorded with null metrics and an `error` note rather than killing the run.
- `build_portfolio_stats()` and `parse_cloc_sum()` are PURE/offline so they can
  be unit-tested without GitHub or cloning (see .tmp/test_portfolio_stats.py).

LoC / doc-line counts come from `cloc --json` run over a shallow clone of each
repo. cloc reports per-language plus a `SUM` block with `code` (→ loc) and
`comment` (→ doc_lines) line counts. scc/tokei are drop-in alternatives if cloc
is ever unavailable — both also report code + comment separately.

Run locally:
    PAT_GITHUB=ghp_xxx python .github/scripts/portfolio_stats.py
    # writes stats/portfolio-<this-month>.json under the current directory
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from github import Github, GithubException

SCHEMA_VERSION = "portfolio-stats/v1"
GENERATED_FOR = "daily-work-summary"

# Shallow-clone timeout per repo (seconds). A repo that hangs past this is
# recorded with an error note and skipped, so one bad repo can't stall the job.
CLONE_TIMEOUT = 300
CLOC_TIMEOUT = 300


# ----------------------------------------------------------------------
# Pure / offline helpers (unit-tested without GitHub or cloning)
# ----------------------------------------------------------------------

def parse_cloc_sum(cloc_json: dict) -> tuple[int, int]:
    """Extract (code_lines, comment_lines) from a `cloc --json` payload.

    cloc's JSON has a top-level "SUM" object: {blank, comment, code, nFiles}.
    Returns (0, 0) for anything missing/malformed so a weird cloc output can
    never raise. code → loc, comment → doc_lines.
    """
    if not isinstance(cloc_json, dict):
        return 0, 0
    total = cloc_json.get("SUM")
    if not isinstance(total, dict):
        return 0, 0
    try:
        code = int(total.get("code", 0) or 0)
    except (TypeError, ValueError):
        code = 0
    try:
        comment = int(total.get("comment", 0) or 0)
    except (TypeError, ValueError):
        comment = 0
    return code, comment


def build_portfolio_stats(
    repo_entries: list[dict],
    period: str,
    generated_at: str,
    schema: str = SCHEMA_VERSION,
) -> dict:
    """Assemble the final artifact dict from already-collected per-repo entries.

    Pure: takes a list of repo dicts (each with at least name/owner/loc/
    doc_lines/last_commit_date/status), sorts them by LoC descending, and
    computes the aggregate block. No I/O, no network — unit-testable.
    """
    repos = sorted(
        repo_entries,
        key=lambda r: (r.get("loc") or 0),
        reverse=True,
    )
    active = [r for r in repos if r.get("status") == "active"]
    archived = [r for r in repos if r.get("status") == "archived"]
    total_loc = sum((r.get("loc") or 0) for r in repos)
    total_doc = sum((r.get("doc_lines") or 0) for r in repos)

    return {
        "schema": schema,
        "generated_for": GENERATED_FOR,
        "period": period,
        "generated_at": generated_at,
        "aggregate": {
            "repo_count": len(repos),
            "active_repo_count": len(active),
            "archived_repo_count": len(archived),
            "total_loc": total_loc,
            "total_doc_lines": total_doc,
        },
        "repos": repos,
    }


def _resolve_period() -> str:
    """Return the YYYY-MM period label. Override with STATS_MONTH for testing
    or a one-off backfill; otherwise the current UTC month."""
    override = (os.environ.get("STATS_MONTH") or "").strip()
    if override:
        try:
            datetime.strptime(override, "%Y-%m")
            return override
        except ValueError:
            print(f"WARNING: STATS_MONTH='{override}' is not YYYY-MM; using current month")
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ----------------------------------------------------------------------
# GitHub + measurement
# ----------------------------------------------------------------------

def get_token() -> str:
    token = os.environ.get("PAT_GITHUB")
    if not token:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            token = os.environ.get("PAT_GITHUB")
        except ImportError:
            pass
    if not token:
        print("ERROR: PAT_GITHUB not set.")
        print("  GitHub Actions: add PAT_GITHUB to repository secrets")
        print("  Local testing:  export PAT_GITHUB=ghp_your_token")
        sys.exit(1)
    return token


def measure_repo_loc(clone_dir: str) -> tuple[int, int]:
    """Run cloc over a checked-out repo and return (loc, doc_lines).

    Never raises: if cloc is missing, errors, or emits unparseable output,
    returns (0, 0) so the repo is still recorded (with zero metrics) rather
    than aborting the whole run.
    """
    try:
        proc = subprocess.run(
            ["cloc", "--json", "--quiet", clone_dir],
            capture_output=True,
            text=True,
            timeout=CLOC_TIMEOUT,
        )
    except FileNotFoundError:
        print("    cloc not found on PATH — recording 0 LoC")
        return 0, 0
    except subprocess.TimeoutExpired:
        print("    cloc timed out — recording 0 LoC")
        return 0, 0

    # cloc exits non-zero / prints nothing for an empty repo (no source files).
    out = (proc.stdout or "").strip()
    if not out:
        return 0, 0
    try:
        return parse_cloc_sum(json.loads(out))
    except json.JSONDecodeError:
        print("    cloc output was not valid JSON — recording 0 LoC")
        return 0, 0


def collect_repo_entry(repo, token: str, workroot: str) -> dict:
    """Shallow-clone one repo, measure it, and return its stats dict.

    Fully wrapped: any failure yields an entry with null loc/doc_lines and an
    `error` note, so the aggregate still reflects every repo's existence.
    """
    full_name = repo.full_name
    owner, name = full_name.split("/", 1)
    status = "archived" if repo.archived else "active"
    last_commit = None
    try:
        # pushed_at is the last push to any branch — a good "last activity" proxy
        # without an extra API call per repo. Date only (UTC) for stable output.
        if repo.pushed_at:
            last_commit = repo.pushed_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        last_commit = None

    entry = {
        "name": name,
        "owner": owner,
        "loc": None,
        "doc_lines": None,
        "last_commit_date": last_commit,
        "status": status,
    }

    clone_dir = os.path.join(workroot, full_name.replace("/", "__"))
    auth_url = f"https://x-access-token:{token}@github.com/{full_name}.git"
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", auth_url, clone_dir],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT,
        )
        if result.returncode != 0:
            # Don't echo stderr verbatim — it can contain the tokenized URL.
            entry["error"] = "clone failed"
            print(f"  {full_name}: clone failed (rc={result.returncode})")
            return entry

        loc, doc_lines = measure_repo_loc(clone_dir)
        entry["loc"] = loc
        entry["doc_lines"] = doc_lines
        print(f"  {full_name}: {loc} loc, {doc_lines} doc ({status})")
    except subprocess.TimeoutExpired:
        entry["error"] = "clone timed out"
        print(f"  {full_name}: clone timed out")
    except Exception as e:
        entry["error"] = type(e).__name__
        print(f"  {full_name}: error ({type(e).__name__})")
    finally:
        shutil.rmtree(clone_dir, ignore_errors=True)

    return entry


def main() -> None:
    print("=" * 50)
    print("Portfolio Stats Generator")
    print("=" * 50)

    token = get_token()
    period = _resolve_period()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Period: {period}")

    from github import Auth
    g = Github(auth=Auth.Token(token), per_page=100)
    try:
        user = g.get_user()
        print(f"Authenticated as: {user.login}")
        repos = list(user.get_repos(affiliation="owner,organization_member"))
    except GithubException as e:
        if e.status in (401, 403):
            print(f"ERROR: PAT_GITHUB rejected ({e.status}). Needs `repo` + `read:user`.")
            sys.exit(1)
        raise
    print(f"Found {len(repos)} repositories")

    entries: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="portfolio-stats-") as workroot:
        for repo in repos:
            entries.append(collect_repo_entry(repo, token, workroot))

    stats = build_portfolio_stats(entries, period, generated_at)

    # Output path: the workflow points PORTFOLIO_STATS_OUTPUT at the
    # coordination-repo clone's stats/ file. Locally it defaults under cwd.
    out_path = (os.environ.get("PORTFOLIO_STATS_OUTPUT") or "").strip()
    if not out_path:
        out_path = str(Path("stats") / f"portfolio-{period}.json")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, indent=2) + "\n")

    agg = stats["aggregate"]
    print(
        f"\nWrote {out} — {agg['repo_count']} repos "
        f"({agg['active_repo_count']} active, {agg['archived_repo_count']} archived), "
        f"{agg['total_loc']:,} loc, {agg['total_doc_lines']:,} doc lines"
    )

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"stats_file={out.as_posix()}\n")
            fh.write(f"period={period}\n")


if __name__ == "__main__":
    main()
