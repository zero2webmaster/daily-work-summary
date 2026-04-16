#!/usr/bin/env python3
"""
Daily Cursor Work Summary Generator

Scans all repos the authenticated account can access (personal + org),
collects commits from the last 24 hours, and generates a conversational
repo-by-repo summary with 3-5 bullets per project.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from github import Github, GithubException, RateLimitExceededException
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)

try:
    import markdown as markdown_lib
except ImportError:
    print("ERROR: markdown not installed. Run: pip install markdown")
    sys.exit(1)

MAX_MSG_LENGTH = 100
MAX_RETRIES = 3
SUMMARY_DIR = "summaries"
HTML_FONT_SIZE = "18px"
NO_WORK_MESSAGE = "No work today – hope you enjoyed the rest!"


def _get_gh_cli_token() -> str | None:
    """Best-effort fallback to GitHub CLI auth integration."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    token = result.stdout.strip()
    return token or None


def get_github_client() -> Github:
    """Build a GitHub client from PAT or GitHub CLI integration."""
    token = os.environ.get("PAT_GITHUB")
    if not token:
        try:
            from dotenv import load_dotenv

            load_dotenv()
            token = os.environ.get("PAT_GITHUB")
        except ImportError:
            pass

    if not token:
        token = _get_gh_cli_token()
        if token:
            print("Using GitHub CLI integration token for API access.")

    if not token:
        print("ERROR: No GitHub token available.")
        print("  Preferred: PAT_GITHUB in secrets/environment")
        print("  Fallback: authenticated GitHub CLI via `gh auth login`")
        sys.exit(1)

    from github import Auth

    return Github(auth=Auth.Token(token), per_page=100)


def truncate(msg: str, length: int = MAX_MSG_LENGTH) -> str:
    first_line = msg.split("\n")[0].strip()
    if len(first_line) <= length:
        return first_line
    return first_line[: length - 3] + "..."


def fetch_commits_with_retry(repo, since, author, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            commits = list(repo.get_commits(since=since, author=author))
            return commits
        except RateLimitExceededException:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Rate limit exceeded after {retries} retries, skipping {repo.full_name}")
                return []
        except GithubException as e:
            if e.status == 409:
                return []
            if e.status == 403 and attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  403 error on {repo.full_name}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Error fetching {repo.full_name}: {e.status} {e.data}")
                return []
    return []


# AI provider config: (api_key_env, model). Gemini also accepts GEMINI_API_KEY.
AI_PROVIDERS = {
    "openrouter": ("OPENROUTER_API_KEY", "anthropic/claude-3-5-haiku"),
    "anthropic": ("ANTHROPIC_API_KEY", "claude-3-5-haiku-20241022"),
    "gemini": ("GOOGLE_API_KEY", "gemini-1.5-flash"),  # GOOGLE_API_KEY or GEMINI_API_KEY
    "openai": ("OPENAI_API_KEY", "gpt-4o-mini"),
}


def _get_ai_client_and_key() -> tuple[str | None, str | None, str | None]:
    """Return (provider, api_key, model) if AI is configured, else (None, None, None)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    provider = (os.environ.get("AI_PROVIDER") or "").lower().strip()
    if not provider:
        for p, (key_env, model) in AI_PROVIDERS.items():
            if os.environ.get(key_env):
                print(f"  AI provider auto-detected: {p}")
                return p, os.environ.get(key_env), model
        return None, None, None

    if provider not in AI_PROVIDERS:
        valid = ", ".join(AI_PROVIDERS.keys())
        print(f"  AI summary: skipped (AI_PROVIDER='{provider}' is not valid; must be one of: {valid})")
        return None, None, None

    key_env, model = AI_PROVIDERS[provider]
    api_key = os.environ.get(key_env) or (os.environ.get("GEMINI_API_KEY") if provider == "gemini" else None)
    if not api_key:
        return None, None, None

    return provider, api_key, model


def _normalize_bullets(text: str) -> list[str]:
    """Turn model output into clean 3-5 bullet strings."""
    seen: set[str] = set()
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", line).strip()
        if not line:
            continue
        line = line.rstrip(".")
        if line.lower() in seen:
            continue
        seen.add(line.lower())
        bullets.append(line)
    return bullets[:5]


def _clean_commit_message(msg: str) -> str:
    line = msg.split("\n")[0].strip()
    # Strip common version prefixes and conventional prefixes to keep summaries readable.
    line = re.sub(r"^v?\d+\.\d+\.\d+\s*[-:]\s*", "", line, flags=re.IGNORECASE)
    line = re.sub(r"^(feat|fix|refactor|docs|chore|test|perf|build|ci)\s*:\s*", "", line, flags=re.IGNORECASE)
    return line.strip() or truncate(msg)


def _categorize_message(msg: str) -> str:
    m = msg.lower()
    if any(k in m for k in ("fix", "bug", "hotfix", "patch", "resolve")):
        return "fix"
    if any(k in m for k in ("refactor", "cleanup", "restructure", "rename")):
        return "refactor"
    if any(k in m for k in ("feat", "add", "implement", "introduce", "ship")):
        return "feature"
    if any(k in m for k in ("perf", "optimiz", "speed", "cache", "latency")):
        return "performance"
    if any(k in m for k in ("test", "spec", "coverage")):
        return "test"
    if any(k in m for k in ("doc", "readme", "guide", "roadmap")):
        return "docs"
    if any(k in m for k in ("deploy", "infra", "docker", "workflow", "ci", "cloud")):
        return "infra"
    if any(k in m for k in ("bump", "deps", "dependency", "chore", "format")):
        return "maintenance"
    return "general"


def _fallback_repo_bullets(messages: list[str], commit_count: int) -> list[str]:
    buckets: dict[str, list[str]] = defaultdict(list)
    used: set[str] = set()

    for msg in messages:
        cleaned = truncate(_clean_commit_message(msg), 110)
        category = _categorize_message(cleaned)
        if cleaned not in buckets[category]:
            buckets[category].append(cleaned)

    category_labels = {
        "feature": "Feature progress",
        "fix": "Bug-fix progress",
        "refactor": "Refactor progress",
        "performance": "Performance work",
        "infra": "Infrastructure updates",
        "test": "Testing hardening",
        "docs": "Documentation updates",
        "maintenance": "Maintenance work",
        "general": "Delivery highlights",
    }

    sorted_categories = sorted(
        buckets.keys(),
        key=lambda c: len(buckets[c]),
        reverse=True,
    )

    bullets: list[str] = []
    for category in sorted_categories:
        examples = [e for e in buckets[category] if e not in used][:2]
        if not examples:
            continue
        used.update(examples)
        bullets.append(f"{category_labels[category]}: {'; '.join(examples)}")
        if len(bullets) >= 4:
            break

    if len(bullets) < 3:
        for msg in messages:
            cleaned = truncate(_clean_commit_message(msg), 110)
            if cleaned in used:
                continue
            bullets.append(f"Key accomplishment: {cleaned}")
            used.add(cleaned)
            if len(bullets) >= 3:
                break

    bullets.append(f"Accomplishment: shipped {commit_count} commit{'s' if commit_count != 1 else ''} in the last 24 hours")
    return bullets[:5]


def generate_ai_repo_bullets(
    messages: list[str],
    repo_full_name: str,
    provider: str,
    api_key: str,
    model: str,
) -> list[str] | None:
    commit_list = "\n".join(truncate(_clean_commit_message(m), 120) for m in messages[:30])
    prompt = f"""You are writing a conversational daily engineering recap.

Repository: {repo_full_name}

Create 3-5 concise bullets describing accomplishments from these commits.
Focus on feature delivery, refactors, bug fixes, and concrete outcomes.

Rules:
- Return ONLY bullet content, one bullet per line (no numbering or markdown fences)
- Do not mention commit counts
- Keep each bullet under 120 characters
- Keep tone conversational and clear

Commits:
{commit_list}
"""
    try:
        if provider == "openrouter":
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=240,
            )
            text = response.choices[0].message.content.strip()
        elif provider == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=240,
            )
            text = response.choices[0].message.content.strip()
        elif provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=240,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
        elif provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=240),
            )
            text = response.text.strip()
        else:
            return None

        bullets = _normalize_bullets(text)
        if len(bullets) < 3:
            return None
        return bullets[:5]
    except Exception as e:
        print(f"  AI summary error ({provider}) for {repo_full_name}: {e}")
        return None


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data."""
    g = get_github_client()
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    display_date = datetime.now(timezone.utc).strftime("%a %b %d, %Y")
    print(f"Fetching commits since: {since.isoformat()}")

    repos = list(user.get_repos(affiliation="owner,organization_member"))
    print(f"Found {len(repos)} repositories")

    active_repos: list[dict[str, Any]] = []
    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login)
        if not commits:
            continue

        messages = [c.commit.message for c in commits]
        owner, repo_name = repo.full_name.split("/", 1)
        active_repos.append(
            {
                "full_name": repo.full_name,
                "url": repo.html_url,
                "owner": owner,
                "repo_name": repo_name,
                "commits": len(commits),
                "messages": messages,
            }
        )
        print(f"  {repo.full_name}: {len(commits)} commits")

    # No commits — return minimal result
    if not active_repos:
        lines = [
            f"# Daily Cursor Work - {display_date}",
            "",
            NO_WORK_MESSAGE,
            "",
            f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        ]
        markdown_body = "\n".join(lines)
        html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
        html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'
        return {
            "html": html,
            "markdown": markdown_body,
            "date": today,
            "total_commits": 0,
            "total_repos": 0,
            "repos": [],
            "ai_summaries_text": "",
            "has_commits": False,
        }

    active_repos.sort(key=lambda r: (-r["commits"], r["full_name"].lower()))
    total_commits = sum(repo["commits"] for repo in active_repos)
    total_repos = len(active_repos)

    ai_provider, ai_key, ai_model = _get_ai_client_and_key()
    if ai_provider and ai_key and ai_model:
        print(f"AI bullets enabled with {ai_provider}/{ai_model}")
    else:
        print("AI bullets disabled; using deterministic fallback summaries.")

    lines = [
        f"# Daily Cursor Work - {display_date}",
        "",
        f"Last 24 hours: **{total_commits} commits** across **{total_repos} repositories**.",
        "",
        "---",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []

    for repo in active_repos:
        full_name = repo["full_name"]
        messages = repo["messages"]
        commit_count = repo["commits"]

        bullets: list[str] | None = None
        if ai_provider and ai_key and ai_model:
            bullets = generate_ai_repo_bullets(messages, full_name, ai_provider, ai_key, ai_model)
        if not bullets:
            bullets = _fallback_repo_bullets(messages, commit_count)

        # Ensure exactly 3-5 bullets for requested summary shape.
        while len(bullets) < 3:
            bullets.append("Progress continued across active development work in this repository")
        bullets = bullets[:5]

        lines.append(f"## {full_name}")
        for bullet in bullets:
            lines.append(f"- {bullet}")
        lines.append("")

        ai_summary = bullets[0] if bullets else None
        ai_summary_bullets.append(f"- {full_name}: {' | '.join(bullets[:3])}")
        structured_repos.append(
            {
                "full_name": full_name,
                "url": repo["url"],
                "owner": repo["owner"],
                "commits": commit_count,
                "messages": messages,
                "ai_summary": ai_summary,
                "summary_bullets": bullets,
            }
        )

    lines.extend(
        [
            "---",
            "",
            "Daily Work Summary initially created by [Zero2Webmaster Founder Dr. Kerry Kriger](https://zero2webmaster.com/kerry-kriger)",
            "",
            "Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary",
            "",
            f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
        ]
    )

    markdown_body = "\n".join(lines)
    html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
    html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'

    return {
        "html": html,
        "markdown": markdown_body,
        "date": today,
        "total_commits": total_commits,
        "total_repos": total_repos,
        "repos": structured_repos,
        "ai_summaries_text": "\n".join(ai_summary_bullets),
        "has_commits": True,
    }


# ------------------------------------------------------------------
# Delivery method parsing
# ------------------------------------------------------------------

VALID_DELIVERY_METHODS = {"email", "airtable", "slack", "discord"}


def parse_delivery_methods(raw: str | None) -> set[str]:
    """Parse DELIVERY_METHOD env var into a set of method names.

    Supports comma-separated values and the legacy 'both' alias.
    Returns {'email'} as the default if nothing valid is set.
    """
    raw = (raw or "email").lower().strip()
    # Backward-compatible alias
    if raw == "both":
        raw = "email,airtable"

    methods = {m.strip() for m in raw.split(",") if m.strip()}
    unknown = methods - VALID_DELIVERY_METHODS
    if unknown:
        valid_str = ", ".join(sorted(VALID_DELIVERY_METHODS))
        print(f"  WARNING: Unknown DELIVERY_METHOD value(s): {', '.join(sorted(unknown))} — ignoring. "
              f"Valid options: {valid_str}")
        methods -= unknown

    if not methods:
        print("  WARNING: No valid delivery methods found, defaulting to 'email'")
        return {"email"}

    return methods


# ------------------------------------------------------------------
# Slack / Discord delivery
# ------------------------------------------------------------------

def send_to_slack(summary_data: dict) -> bool:
    """Send summary to Slack webhook. Returns True on success."""
    from webhook_client import send_slack

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("  Slack: skipped (SLACK_WEBHOOK_URL not set)")
        return False

    print("  Slack: sending message...")
    return send_slack(webhook_url, summary_data)


def send_to_discord(summary_data: dict) -> bool:
    """Send summary to Discord webhook. Returns True on success."""
    from webhook_client import send_discord

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("  Discord: skipped (DISCORD_WEBHOOK_URL not set)")
        return False

    print("  Discord: sending message...")
    return send_discord(webhook_url, summary_data)


# ------------------------------------------------------------------
# Airtable delivery
# ------------------------------------------------------------------

def _get_airtable_config() -> dict[str, str] | None:
    """Return Airtable config dict if all required vars are set, else None."""
    pat = os.environ.get("AIRTABLE_PAT")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_summaries = os.environ.get("AIRTABLE_TABLE_SUMMARIES")
    table_repos = os.environ.get("AIRTABLE_TABLE_REPOS")

    if not all([pat, base_id, table_summaries, table_repos]):
        missing = []
        if not pat:
            missing.append("AIRTABLE_PAT")
        if not base_id:
            missing.append("AIRTABLE_BASE_ID")
        if not table_summaries:
            missing.append("AIRTABLE_TABLE_SUMMARIES")
        if not table_repos:
            missing.append("AIRTABLE_TABLE_REPOS")
        print(f"  Airtable: skipped (missing: {', '.join(missing)})")
        return None

    return {
        "pat": pat,
        "base_id": base_id,
        "table_summaries": table_summaries,
        "table_repos": table_repos,
    }


def write_to_airtable(summary_data: dict[str, Any]) -> bool:
    """Write summary data to Airtable. Returns True on success."""
    from airtable_client import AirtableClient, AirtableError

    config = _get_airtable_config()
    if not config:
        return False

    client = AirtableClient(pat=config["pat"], base_id=config["base_id"])
    tbl_summaries = config["table_summaries"]
    tbl_repos = config["table_repos"]

    date_str = summary_data["date"]

    # --- Find or create Repository records (always, even if summary exists) ---
    repo_record_ids: list[str] = []
    repos = summary_data.get("repos", [])
    if not repos:
        print("  Airtable: no repos in summary (no commits today?)")
    for repo_info in repos:
        repo_record_id = _find_or_create_repo(client, tbl_repos, repo_info)
        if repo_record_id:
            repo_record_ids.append(repo_record_id)
    if repos:
        print(f"  Airtable: {len(repo_record_ids)}/{len(repos)} repo records ready for linking")

    # --- Duplicate detection: did we already create today's summary? ---
    existing_record = None
    try:
        existing = client.query_records(
            tbl_summaries,
            filter_formula=f"{{Timestamp}}='{date_str}'",
            max_records=1,
        )
        if existing:
            existing_record = existing[0]
    except AirtableError as exc:
        print(f"  Airtable: warning checking for duplicates: {exc}")

    fields: dict[str, Any] = {
        "Timestamp": date_str,
        "Date": date_str,
        "Summary": summary_data["markdown"],
        "Repos Worked On": summary_data["total_repos"],
        "Total Commits": summary_data["total_commits"],
        "AI Summaries": summary_data["ai_summaries_text"] or "(AI summaries not enabled)",
    }
    if repo_record_ids:
        fields["Repositories"] = repo_record_ids

    def _write_summary(with_repos: bool = True) -> bool:
        f = fields.copy()
        if not with_repos and "Repositories" in f:
            del f["Repositories"]
        if existing_record:
            client.update_record(tbl_summaries, existing_record["id"], f)
            return True
        record = client.create_record(tbl_summaries, f)
        print(f"  Airtable: created daily summary record {record['id']} for {date_str}")
        return True

    if existing_record:
        # Summary exists — update it to add/refresh repo links (backfill if missing)
        try:
            _write_summary(with_repos=True)
            print(f"  Airtable: updated existing summary {existing_record['id']} for {date_str} (repos linked)")
            return True
        except AirtableError as exc:
            if getattr(exc, "status_code", None) == 422:
                try:
                    _write_summary(with_repos=False)
                    print(f"  Airtable: updated summary (Repositories field missing — run Setup Airtable to add it)")
                    return True
                except AirtableError:
                    pass
            print(f"  Airtable: warning updating summary: {exc}")
            return True  # Summary exists, don't fail the run

    # --- Create new Daily Summary record ---
    try:
        _write_summary(with_repos=True)
        return True
    except AirtableError as exc:
        if getattr(exc, "status_code", None) == 422:
            try:
                _write_summary(with_repos=False)
                print(f"  Airtable: created summary (Repositories link field missing — run Setup Airtable)")
                return True
            except AirtableError as retry_exc:
                print(f"  Airtable ERROR creating summary: {retry_exc}")
                return False
        print(f"  Airtable ERROR creating summary: {exc}")
        return False


def _find_or_create_repo(
    client: "AirtableClient", table_id: str, repo_info: dict
) -> str | None:
    """Find an existing repo record by name, or create one. Returns record ID."""
    from airtable_client import AirtableError

    full_name = repo_info["full_name"]

    try:
        existing = client.query_records(
            table_id,
            filter_formula=f"{{Name}}='{full_name}'",
            max_records=1,
        )
        if existing:
            return existing[0]["id"]
    except AirtableError as exc:
        print(f"  Airtable: warning looking up repo '{full_name}': {exc}")

    try:
        record = client.create_record(table_id, {
            "Name": full_name,
            "URL": repo_info["url"],
            "Owner": repo_info["owner"],
        })
        print(f"  Airtable: created repo record for {full_name}")
        return record["id"]
    except AirtableError as exc:
        print(f"  Airtable ERROR creating repo '{full_name}': {exc}")
        return None


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    print("=" * 50)
    print("Daily Work Summary Generator")
    print("=" * 50)

    try:
        summary_data = generate_summary()
    except GithubException as e:
        if e.status == 401:
            print("ERROR: PAT_GITHUB is invalid or expired.")
            print("  Regenerate at: https://github.com/settings/tokens")
            sys.exit(1)
        elif e.status == 403:
            print("ERROR: PAT_GITHUB has insufficient permissions.")
            print("  Required scopes: repo, read:user")
            print("  Update at: https://github.com/settings/tokens")
            sys.exit(1)
        else:
            raise

    # Determine delivery methods (comma-separated, 'both' = email+airtable)
    delivery_methods = parse_delivery_methods(os.environ.get("DELIVERY_METHOD"))
    print(f"\nDelivery methods: {', '.join(sorted(delivery_methods))}")

    # Write summary files (always, for archive and email step)
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    summary_markdown_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.md"
    summary_html_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.html"
    summary_markdown_path.write_text(summary_data["markdown"], encoding="utf-8")
    summary_html_path.write_text(summary_data["html"], encoding="utf-8")
    print(f"Markdown summary written to: {summary_markdown_path}")
    print(f"HTML summary written to: {summary_html_path}")

    # Airtable delivery
    if "airtable" in delivery_methods and summary_data["has_commits"]:
        print("\n--- Airtable Delivery ---")
        write_to_airtable(summary_data)

    # Slack delivery
    if "slack" in delivery_methods:
        print("\n--- Slack Delivery ---")
        send_to_slack(summary_data)

    # Discord delivery
    if "discord" in delivery_methods:
        print("\n--- Discord Delivery ---")
        send_to_discord(summary_data)

    # Tell the workflow whether to run the email step.
    has_summary = summary_markdown_path.exists() and summary_markdown_path.stat().st_size > 0
    send_email = has_summary and "email" in delivery_methods
    if not send_email:
        active = ", ".join(sorted(delivery_methods - {"email"}))
        reason = f"delivery is {active} only" if active else "summary file not generated"
        print(f"\n  Email step: skipped ({reason})")

    # Write outputs for the workflow to consume
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"send_email={'true' if send_email else 'false'}\n")
            fh.write(f"has_summary={'true' if has_summary else 'false'}\n")
            fh.write(f"summary_markdown_file={summary_markdown_path}\n")
            fh.write(f"summary_html_file={summary_html_path}\n")
            # Backward-compatible output key expected by older workflow versions.
            fh.write(f"summary_file={summary_html_path}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
