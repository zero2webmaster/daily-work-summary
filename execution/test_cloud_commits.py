"""Regression test: commits from Claude Code cloud sessions are counted (v2.1.0).

The complaint (commerce-engine, 2026-11-08, relaying Kerry): he worked mostly
from his phone on 2026-11-07 and the email showed almost none of it. Phone
sessions commit as `Claude <noreply@anthropic.com>`, which GitHub can't link to
his login, and the digest filtered every repo to `author=<login>`. 27 commits
were dropped that day.

These checks pin:
  1. Claude-authored commits are fetched alongside the user's own, by default.
  2. A commit returned for both identities appears once (merge by sha).
  3. The merged list is newest-first, like a single get_commits call.
  4. EXTRA_COMMIT_AUTHORS overrides the list, and `none` restores login-only.
  5. One identity failing doesn't hide the other's commits.

Run:  python3 execution/test_cloud_commits.py
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".github" / "scripts"))

os.environ.pop("EXTRA_COMMIT_AUTHORS", None)

import generate_summary as gs  # noqa: E402
from github import GithubException  # noqa: E402

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got:  {got}\n          want: {want}")
        failures.append(name)


def commit(sha: str, hour: int):
    when = datetime(2026, 11, 7, hour, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        sha=sha,
        commit=SimpleNamespace(message=f"commit {sha}", committer=SimpleNamespace(date=when)),
    )


class FakeRepo:
    """Answers get_commits(author=...) from a per-identity table."""

    full_name = "zero2webmaster/commerce-engine"

    def __init__(self, by_author, fail_for=()):
        self.by_author = by_author
        self.fail_for = set(fail_for)
        self.asked: list[str] = []

    def get_commits(self, since=None, author=None, until=None):
        self.asked.append(author)
        if author in self.fail_for:
            raise GithubException(500, {"message": "boom"}, None)
        return list(self.by_author.get(author, []))


LOGIN = "kerrykriger"
CLAUDE = "noreply@anthropic.com"
SINCE = datetime(2026, 11, 7, tzinfo=timezone.utc)


print("\n1. get_extra_commit_authors — defaults and overrides")

check("unset → Claude cloud identity", gs.get_extra_commit_authors(), [CLAUDE])
for val, want in [
    ("", [CLAUDE]),
    ("none", []),
    ("OFF", []),
    ("bot@example.com, someone ", ["bot@example.com", "someone"]),
    ("a@x.com,A@X.com", ["a@x.com"]),
]:
    os.environ["EXTRA_COMMIT_AUTHORS"] = val
    check(f"EXTRA_COMMIT_AUTHORS={val!r}", gs.get_extra_commit_authors(), want)
os.environ.pop("EXTRA_COMMIT_AUTHORS", None)


print("\n2. fetch_work_commits — Kerry's 2026-11-07 shape")

laptop = [commit("mac2", 15), commit("mac1", 14)]
phone = [commit(f"cl{i}", 16 + i) for i in range(5)][::-1]
repo = FakeRepo({LOGIN: laptop, CLAUDE: phone})
got = gs.fetch_work_commits(repo, SINCE, LOGIN, [CLAUDE])
check("both identities queried", repo.asked, [LOGIN, CLAUDE])
check("all 7 commits counted (was 2)", len(got), 7)
check("newest first across identities",
      [c.sha for c in got], ["cl4", "cl3", "cl2", "cl1", "cl0", "mac2", "mac1"])


print("\n3. Same commit returned twice is counted once")

shared = commit("both", 12)
repo = FakeRepo({LOGIN: [shared], CLAUDE: [shared, commit("cl", 13)]})
got = gs.fetch_work_commits(repo, SINCE, LOGIN, [CLAUDE])
check("deduplicated by sha", sorted(c.sha for c in got), ["both", "cl"])


print("\n4. Disabled → login only, one query, order untouched")

repo = FakeRepo({LOGIN: laptop, CLAUDE: phone})
got = gs.fetch_work_commits(repo, SINCE, LOGIN, [])
check("only the login is queried", repo.asked, [LOGIN])
check("same list as before v2.1.0", [c.sha for c in got], ["mac2", "mac1"])

repo = FakeRepo({LOGIN: laptop})
gs.fetch_work_commits(repo, SINCE, LOGIN, ["KerryKriger"])
check("extra identity equal to the login is not queried twice", repo.asked, [LOGIN])


print("\n5. One identity erroring doesn't hide the other")

repo = FakeRepo({LOGIN: laptop, CLAUDE: phone}, fail_for={CLAUDE})
got = gs.fetch_work_commits(repo, SINCE, LOGIN, [CLAUDE])
check("login commits still returned", [c.sha for c in got], ["mac2", "mac1"])

repo = FakeRepo({LOGIN: laptop, CLAUDE: phone}, fail_for={LOGIN})
got = gs.fetch_work_commits(repo, SINCE, LOGIN, [CLAUDE])
check("Claude commits still returned", len(got), 5)


print("\n6. Both workflows pass the setting through")

root = Path(__file__).resolve().parent.parent / ".github" / "workflows"
for wf in ("daily-summary.yml", "backfill-summaries.yml"):
    text = (root / wf).read_text()
    check(f"{wf} forwards EXTRA_COMMIT_AUTHORS",
          "EXTRA_COMMIT_AUTHORS: ${{ vars.EXTRA_COMMIT_AUTHORS }}" in text, True)


print()
if failures:
    print(f"{len(failures)} check(s) FAILED")
    sys.exit(1)
print("All cloud-commit checks passed.")
