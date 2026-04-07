#!/usr/bin/env python3
"""
Daily Work Summary Generator

Fetches all commits from the last 24 hours across every repository
the authenticated GitHub user owns, then generates a smart grouped
summary as Markdown with optional AI-powered repo descriptions.

Supports multiple delivery methods controlled by the DELIVERY_METHOD
environment variable (comma-separated list):
  email    — send HTML email via Gmail SMTP (workflow step)
  airtable — write to Airtable tables
  slack    — POST to Slack incoming webhook (SLACK_WEBHOOK_URL)
  discord  — POST to Discord incoming webhook (DISCORD_WEBHOOK_URL)
  both     — alias for "email,airtable" (backward-compatible)

Examples:
  DELIVERY_METHOD=email
  DELIVERY_METHOD=slack,discord
  DELIVERY_METHOD=email,slack,airtable

Runs as part of the GitHub Actions workflow, but can also be tested
locally with PAT_GITHUB set in environment or .env file.
"""

import os
import re
import sys
import time
import json
import subprocess
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

MAX_MSG_LENGTH = 80
MAX_RETRIES = 3
SUMMARY_DIR = "summaries"
EMAIL_HTML_DIR = ".tmp"
HTML_FONT_SIZE = "18px"
NO_WORK_MESSAGE = "No work today – hope you enjoyed the rest!"


def get_github_client() -> Github:
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
        print("  GitHub Actions: Add PAT_GITHUB to repository secrets")
        print("  Local testing:  export PAT_GITHUB=ghp_your_token")
        print("  Create token:   https://github.com/settings/tokens")
        sys.exit(1)

    from github import Auth
    return Github(auth=Auth.Token(token), per_page=100)


def truncate(msg: str, length: int = MAX_MSG_LENGTH) -> str:
    first_line = msg.split("\n")[0].strip()
    if len(first_line) <= length:
        return first_line
    return first_line[: length - 3] + "..."


def _classify_commit(msg: str) -> str:
    text = msg.lower()
    if any(k in text for k in ("fix", "bug", "hotfix", "patch", "resolve")):
        return "fixes"
    if any(k in text for k in ("refactor", "cleanup", "restructure", "rename", "simplify")):
        return "refactors"
    if any(k in text for k in ("perf", "optimiz", "speed", "cache")):
        return "performance"
    if any(k in text for k in ("test", "spec", "coverage", "e2e")):
        return "testing"
    if any(k in text for k in ("doc", "readme", "guide", "roadmap", "status")):
        return "docs"
    return "features"


def _bucket_prefix(bucket: str) -> str:
    return {
        "features": "Shipped:",
        "fixes": "Fixed:",
        "refactors": "Refactored:",
        "performance": "Improved performance:",
        "testing": "Strengthened testing:",
        "docs": "Documented:",
    }[bucket]


def _format_bucket_summary(bucket: str, messages: list[str]) -> str:
    top = [truncate(m) for m in messages[:2]]
    summary = "; ".join(top)
    if len(messages) > 2:
        summary += f" (+{len(messages) - 2} more)"
    return f"{_bucket_prefix(bucket)} {summary}"


def build_repo_bullets(messages: list[str], ai_summary: str | None = None) -> list[str]:
    """Build 3-5 conversational bullets from raw commit messages."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for msg in messages:
        buckets[_classify_commit(msg)].append(msg)

    bullets: list[str] = []
    if ai_summary:
        bullets.append(ai_summary)

    ordered_buckets = ["features", "fixes", "refactors", "performance", "testing", "docs"]
    for bucket in ordered_buckets:
        if buckets.get(bucket):
            bullets.append(_format_bucket_summary(bucket, buckets[bucket]))
        if len(bullets) >= 5:
            return bullets[:5]

    # Ensure we always return at least 3 bullets when there is commit activity.
    if len(bullets) < 3:
        for msg in messages:
            line = f"Also tackled: {truncate(msg)}"
            if line not in bullets:
                bullets.append(line)
            if len(bullets) >= 3:
                break

    return bullets[:5]


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
        print("  AI summary: skipped (no provider key found in environment)")
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


def generate_ai_repo_summary(messages: list[str]) -> str | None:
    """Generate a one-sentence summary of the type of work from commit messages."""
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        print("  AI summary: skipped (no provider key configured)")
        return None
    print(f"  AI summary: using {provider}/{model}")

    commit_list = "\n".join(truncate(m) for m in messages[:20])
    prompt = f"""In one sentence, summarize the theme of development work from these git commits. Be concise and professional.

Rules:
- Do NOT list or enumerate commits (e.g., never say "2 changes: X; Y" or "3 commits: A, B, C")
- Do NOT say how many commits there were
- Describe the TYPE of work and WHAT area it touched (e.g., "Authentication refactor and UI polish across the login and dashboard flows.")
- If there is only one commit, still describe the theme, not the commit itself

Commits:
{commit_list}"""

    try:
        if provider == "openrouter":
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            summary = response.choices[0].message.content.strip()

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            summary = response.choices[0].message.content.strip()

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            summary = response.content[0].text.strip()

        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=80),
            )
            summary = response.text.strip()

        else:
            return None

        return summary.rstrip(".")
    except Exception as e:
        print(f"  AI summary error ({provider}): {e}")
        return None


def _build_summary_from_active_repos(active_repos: list[dict[str, Any]], today: str) -> dict[str, Any]:
    """Render markdown/html and metadata from collected active repos."""
    # No commits — return minimal result
    if not active_repos:
        msg = NO_WORK_MESSAGE
        footer = (
            "<p>Daily Work Summary initially created by "
            '<a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>'
            '<p>Contribute to the public repository at: '
            '<a href="https://github.com/zero2webmaster/daily-work-summary">github.com/zero2webmaster/daily-work-summary</a></p>'
        )
        html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;"><p>{msg}</p>{footer}</div>'
        return {
            "html": html,
            "markdown": msg,
            "date": today,
            "total_commits": 0,
            "total_repos": 0,
            "repos": [],
            "ai_summaries_text": "",
            "has_commits": False,
        }

    total_commits = sum(repo_info["commits"] for repo_info in active_repos)
    total_repos = len(active_repos)
    sorted_repos = sorted(active_repos, key=lambda r: r["commits"], reverse=True)

    lines = [
        f"# Daily Cursor Work - {today}",
        "",
        "Here is your daily GitHub recap across personal and zero2webmaster repositories.",
        "",
        f"**{total_commits} commits** across **{total_repos} active repos** in the last 24 hours.",
        "",
        "---",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []

    for repo_info in sorted_repos:
        full_name = repo_info["full_name"]
        count = repo_info["commits"]
        messages = repo_info["messages"]
        ai_summary = generate_ai_repo_summary(messages)
        repo_bullets = build_repo_bullets(messages, ai_summary=ai_summary)

        lines.append(f"## {full_name}")
        lines.append(f"*{count} commit{'s' if count != 1 else ''}*")
        lines.append("")
        for bullet in repo_bullets:
            lines.append(f"- {bullet}")
        lines.append("")

        if ai_summary:
            ai_summary_bullets.append(f"- {full_name}: {ai_summary}")

        structured_repos.append({
            "full_name": full_name,
            "url": repo_info["url"],
            "owner": repo_info["owner"],
            "commits": count,
            "messages": messages,
            "ai_summary": ai_summary,
            "summary_bullets": repo_bullets,
        })

    lines.append("---")
    lines.append("")
    lines.append("Daily Work Summary initially created by [Zero2Webmaster Founder Dr. Kerry Kriger](https://zero2webmaster.com/kerry-kriger)")
    lines.append("")
    lines.append("Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary")
    lines.append("")
    lines.append(f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

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


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data.

    Returns a dict with keys:
        html, markdown, date, total_commits, total_repos,
        repos (list of dicts), ai_summaries_text, has_commits
    """
    g = get_github_client()
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Fetching commits since: {since.isoformat()}")

    active_repos: list[dict[str, Any]] = []

    repos = list(user.get_repos(affiliation="owner,organization_member"))
    print(f"Found {len(repos)} repositories")

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login)
        if commits:
            messages = [c.commit.message for c in commits]
            print(f"  {repo.full_name}: {len(commits)} commits")
            active_repos.append({
                "full_name": repo.full_name,
                "url": repo.html_url,
                "owner": repo.owner.login,
                "commits": len(commits),
                "messages": messages,
            })

    return _build_summary_from_active_repos(active_repos, today)


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


def _gh_cli_json(args: list[str]) -> Any:
    """Run `gh api ...` and parse JSON output."""
    cmd = ["gh", "api", *args]
    output = subprocess.check_output(cmd, text=True)
    return json.loads(output)


def _gh_cli_login_from_status() -> str:
    """Best-effort parse of authenticated login from `gh auth status` output."""
    status = subprocess.check_output(
        ["gh", "auth", "status"], stderr=subprocess.STDOUT, text=True
    )
    match = re.search(r"Logged in to github\.com account (\S+)", status)
    return match.group(1) if match else "integration"


def generate_summary_via_gh_cli() -> dict[str, Any]:
    """Fallback summary generation using GH CLI integration scope."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    login = _gh_cli_login_from_status()
    print(f"Using GH CLI fallback mode (account: {login})")
    print(f"Fetching commits since: {since.isoformat()}")

    try:
        install_data = _gh_cli_json(["/installation/repositories"])
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: Unable to list installation repositories with GH CLI: {exc}")
        return _build_summary_from_active_repos([], today)

    repos = install_data.get("repositories", [])
    print(f"Found {len(repos)} installation repositories")

    active_repos: list[dict[str, Any]] = []
    for repo in repos:
        if repo.get("archived"):
            continue

        full_name = repo["full_name"]
        try:
            commits = _gh_cli_json([
                f"/repos/{full_name}/commits",
                "-f", f"since={since.isoformat()}",
                "-f", "per_page=100",
            ])
        except subprocess.CalledProcessError as exc:
            print(f"  Error fetching commits for {full_name}: {exc}")
            continue

        messages: list[str] = []
        for commit in commits:
            author_login = ((commit.get("author") or {}).get("login") or "").lower()
            committer_login = ((commit.get("committer") or {}).get("login") or "").lower()
            if login.lower() not in (author_login, committer_login):
                continue
            message = ((commit.get("commit") or {}).get("message") or "").strip()
            if message:
                messages.append(message)

        if messages:
            print(f"  {full_name}: {len(messages)} commits")
            active_repos.append({
                "full_name": full_name,
                "url": repo.get("html_url", f"https://github.com/{full_name}"),
                "owner": full_name.split("/", 1)[0],
                "commits": len(messages),
                "messages": messages,
            })

    return _build_summary_from_active_repos(active_repos, today)


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
            print("WARNING: PAT_GITHUB has insufficient permissions for /user.")
            print("  Falling back to GH CLI integration scope.")
            summary_data = generate_summary_via_gh_cli()
        else:
            raise

    # Determine delivery methods (comma-separated, 'both' = email+airtable)
    delivery_methods = parse_delivery_methods(os.environ.get("DELIVERY_METHOD"))
    print(f"\nDelivery methods: {', '.join(sorted(delivery_methods))}")

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

    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    Path(EMAIL_HTML_DIR).mkdir(exist_ok=True)
    archive_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.md"
    email_html_path = Path(EMAIL_HTML_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.html"

    archive_path.write_text(summary_data["markdown"])
    email_html_path.write_text(summary_data["html"])
    print(f"Archive written to: {archive_path}")
    print(f"Email HTML written to: {email_html_path}")

    send_email = "email" in delivery_methods
    if not send_email:
        active = ", ".join(sorted(delivery_methods - {"email"}))
        print(f"\n  Email step: skipped (delivery is {active} only)")

    # Write outputs for the workflow to consume
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write("has_summary=true\n")
            fh.write(f"archive_file={archive_path.as_posix()}\n")
            fh.write(f"summary_file={email_html_path.as_posix()}\n")
            fh.write(f"send_email={'true' if send_email else 'false'}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
