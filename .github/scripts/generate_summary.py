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
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

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
        try:
            gh_token = subprocess.check_output(
                ["gh", "auth", "token"], stderr=subprocess.DEVNULL, text=True
            ).strip()
            if gh_token:
                token = gh_token
                print("Using GitHub CLI auth token fallback")
        except Exception:
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


def get_report_timezone() -> ZoneInfo:
    tz_name = os.environ.get("EMAIL_TIMEZONE", "America/New_York").strip() or "America/New_York"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        print(f"WARNING: Invalid EMAIL_TIMEZONE '{tz_name}', falling back to UTC")
        return ZoneInfo("UTC")


def get_target_repositories(user) -> list:
    """Return de-duplicated personal + organization repositories."""
    repo_map: dict[str, Any] = {}

    personal_repos = list(user.get_repos(type="owner"))
    for repo in personal_repos:
        repo_map[repo.full_name] = repo
    print(f"Personal repos discovered: {len(personal_repos)}")

    orgs = list(user.get_orgs())
    if orgs:
        print(f"Organization memberships discovered: {len(orgs)}")
    for org in orgs:
        try:
            org_repos = list(org.get_repos(type="all"))
            print(f"  {org.login}: {len(org_repos)} repos")
            for repo in org_repos:
                repo_map[repo.full_name] = repo
        except GithubException as e:
            print(f"  Skipping org {org.login}: {e.status} {e.data}")

    repos = list(repo_map.values())
    repos.sort(key=lambda r: r.full_name.lower())
    print(f"Total unique repositories to scan: {len(repos)}")
    return repos


def _cleanup_bullet_text(text: str) -> str:
    cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", text.strip())
    return cleaned.rstrip()


def _normalize_commit_for_summary(msg: str) -> str:
    msg = truncate(msg)
    msg = re.sub(r"^[a-z]+(\([^)]+\))?!?:\s*", "", msg, flags=re.IGNORECASE)
    return msg[:1].upper() + msg[1:] if msg else msg


def _heuristic_repo_bullets(messages: list[str]) -> list[str]:
    categories: dict[str, list[str]] = defaultdict(list)
    ordered_messages = [_normalize_commit_for_summary(m) for m in messages if m.strip()]

    for msg in ordered_messages:
        lower = msg.lower()
        if any(k in lower for k in ("feat", "feature", "add ", "implement", "introduce", "support")):
            categories["feature"].append(msg)
        elif any(k in lower for k in ("fix", "bug", "resolve", "patch", "hotfix")):
            categories["fix"].append(msg)
        elif any(k in lower for k in ("refactor", "cleanup", "clean up", "rename", "restructure")):
            categories["refactor"].append(msg)
        elif any(k in lower for k in ("perf", "optimiz", "cache", "faster", "speed")):
            categories["performance"].append(msg)
        elif any(k in lower for k in ("test", "spec", "coverage", "qa")):
            categories["testing"].append(msg)
        elif any(k in lower for k in ("docs", "readme", "documentation")):
            categories["docs"].append(msg)
        else:
            categories["general"].append(msg)

    bullets: list[str] = []

    if categories["feature"]:
        bullets.append(f"Feature progress: {'; '.join(categories['feature'][:2])}")
    if categories["fix"]:
        bullets.append(f"Bug fixes shipped: {'; '.join(categories['fix'][:2])}")
    if categories["refactor"]:
        bullets.append(f"Refactors landed: {'; '.join(categories['refactor'][:2])}")
    if categories["performance"]:
        bullets.append(f"Performance improvements: {'; '.join(categories['performance'][:2])}")
    if categories["testing"]:
        bullets.append(f"Test coverage updates: {'; '.join(categories['testing'][:2])}")
    if categories["docs"]:
        bullets.append(f"Documentation polish: {'; '.join(categories['docs'][:2])}")

    if not bullets:
        bullets = [f"Shipped work on: {m}" for m in ordered_messages[:5]]

    used_snippets = " ".join(bullets).lower()
    for msg in ordered_messages:
        if len(bullets) >= 5:
            break
        if msg.lower() not in used_snippets:
            bullets.append(f"Additional progress: {msg}")

    while len(bullets) < 3:
        bullets.append("Kept momentum with steady iterative improvements across this project.")

    return [b.rstrip(".") for b in bullets[:5]]


# AI provider config: (api_key_env, model). Gemini also accepts GEMINI_API_KEY.
AI_PROVIDERS = {
    "openrouter": ("OPENROUTER_API_KEY", "anthropic/claude-3-5-haiku"),
    "anthropic": ("ANTHROPIC_API_KEY", "claude-3-5-haiku-20241022"),
    "gemini": ("GOOGLE_API_KEY", "gemini-1.5-flash"),  # GOOGLE_API_KEY or GEMINI_API_KEY
    "openai": ("OPENAI_API_KEY", "gpt-4o-mini"),
}
_AI_CONFIG_CACHE: tuple[str | None, str | None, str | None] | None = None


def _get_ai_client_and_key() -> tuple[str | None, str | None, str | None]:
    """Return (provider, api_key, model) if AI is configured, else (None, None, None)."""
    global _AI_CONFIG_CACHE
    if _AI_CONFIG_CACHE is not None:
        return _AI_CONFIG_CACHE

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
                _AI_CONFIG_CACHE = (p, os.environ.get(key_env), model)
                return _AI_CONFIG_CACHE
        print("  AI summary: skipped (no provider key found in environment)")
        _AI_CONFIG_CACHE = (None, None, None)
        return _AI_CONFIG_CACHE

    if provider not in AI_PROVIDERS:
        valid = ", ".join(AI_PROVIDERS.keys())
        print(f"  AI summary: skipped (AI_PROVIDER='{provider}' is not valid; must be one of: {valid})")
        _AI_CONFIG_CACHE = (None, None, None)
        return _AI_CONFIG_CACHE

    key_env, model = AI_PROVIDERS[provider]
    api_key = os.environ.get(key_env) or (os.environ.get("GEMINI_API_KEY") if provider == "gemini" else None)
    if not api_key:
        _AI_CONFIG_CACHE = (None, None, None)
        return _AI_CONFIG_CACHE

    _AI_CONFIG_CACHE = (provider, api_key, model)
    return _AI_CONFIG_CACHE


def generate_ai_repo_bullets(messages: list[str]) -> list[str] | None:
    """Generate 3-5 conversational bullets that summarize repo work."""
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        return None
    print(f"  AI summary: using {provider}/{model}")

    commit_list = "\n".join(truncate(m) for m in messages[:20])
    prompt = f"""Summarize this repository's work from the commit list below.

Return exactly 3 to 5 concise bullets in a conversational tone.
Each line must start with "• ".
Focus on outcomes (features, fixes, refactors, accomplishments).
Do not mention the number of commits.
Do not add any intro/outro text.

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
                max_tokens=220,
            )
            summary_text = response.choices[0].message.content.strip()

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=220,
            )
            summary_text = response.choices[0].message.content.strip()

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=220,
                messages=[{"role": "user", "content": prompt}],
            )
            summary_text = response.content[0].text.strip()

        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=220),
            )
            summary_text = response.text.strip()

        else:
            return None

        bullets: list[str] = []
        for raw_line in summary_text.splitlines():
            cleaned = _cleanup_bullet_text(raw_line)
            if cleaned:
                bullets.append(cleaned.rstrip("."))

        unique_bullets: list[str] = []
        seen = set()
        for bullet in bullets:
            key = bullet.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_bullets.append(bullet)

        if len(unique_bullets) < 3:
            return None
        return unique_bullets[:5]
    except Exception as e:
        print(f"  AI summary error ({provider}): {e}")
        return None


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data.

    Returns a dict with keys:
        html, markdown, date, total_commits, total_repos,
        repos (list of dicts), ai_summaries_text, has_commits
    """
    g = get_github_client()
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    report_tz = get_report_timezone()
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(report_tz)
    since = now_utc - timedelta(hours=24)
    today = now_local.strftime("%Y-%m-%d")
    print(f"Fetching commits since: {since.isoformat()}")

    repo_activity: list[dict[str, Any]] = []
    repos = get_target_repositories(user)

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login)
        if commits:
            messages = [c.commit.message for c in commits]
            owner, repo_name = repo.full_name.split("/", 1)
            repo_activity.append({
                "full_name": repo.full_name,
                "repo_name": repo_name,
                "owner": owner,
                "url": repo.html_url,
                "messages": messages,
                "commits": len(messages),
            })
            print(f"  {repo.full_name}: {len(commits)} commits")

    # No commits — return minimal result
    if not repo_activity:
        lines = [
            f"# Daily Cursor Work - {today}",
            "",
            NO_WORK_MESSAGE,
            "",
            f"*Generated at {now_local.strftime('%Y-%m-%d %H:%M %Z')}*",
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

    repo_activity.sort(key=lambda item: (-item["commits"], item["full_name"].lower()))
    total_commits = sum(item["commits"] for item in repo_activity)
    total_repos = len(repo_activity)

    lines = [
        f"# Daily Cursor Work - {today}",
        "",
        f"Quick recap: {total_commits} commit{'s' if total_commits != 1 else ''} across {total_repos} active repo{'s' if total_repos != 1 else ''} in the last 24 hours.",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []

    for repo_info in repo_activity:
        full_name = repo_info["full_name"]
        repo_name = repo_info["repo_name"]
        owner = repo_info["owner"]
        count = repo_info["commits"]
        messages = repo_info["messages"]

        ai_bullets = generate_ai_repo_bullets(messages)
        summary_bullets = ai_bullets or _heuristic_repo_bullets(messages)

        lines.append(f"**{repo_name}** ({count} commit{'s' if count != 1 else ''})")
        for bullet in summary_bullets:
            lines.append(f"• {bullet}")
        lines.append("")

        ai_summary_bullets.append(f"- {full_name}: {' | '.join(summary_bullets[:2])}")
        structured_repos.append({
            "full_name": full_name,
            "url": repo_info["url"],
            "owner": owner,
            "commits": count,
            "messages": messages,
            "summary_bullets": summary_bullets,
            "ai_summary": summary_bullets[0] if summary_bullets else None,
        })

    lines.append("")
    lines.append(f"*Generated at {now_local.strftime('%Y-%m-%d %H:%M %Z')}*")
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
    print("Daily Cursor Work Summary Generator")
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

    # Write archive + email files (always generated, even on no-work days)
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    markdown_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.md"
    html_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.html"
    markdown_path.write_text(summary_data["markdown"])
    html_path.write_text(summary_data["html"])
    print(f"Markdown archive written to: {markdown_path}")
    print(f"Email HTML written to: {html_path}")

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

    # Tell the workflow whether to run the email step
    send_email = "email" in delivery_methods
    if not send_email:
        active = ", ".join(sorted(delivery_methods - {"email"}))
        print(f"\n  Email step: skipped (delivery is {active} only)")

    # Write outputs for the workflow to consume
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            has_summary = bool(summary_data["markdown"].strip())
            fh.write(f"has_summary={'true' if has_summary else 'false'}\n")
            fh.write(f"send_email={'true' if send_email else 'false'}\n")
            fh.write(f"summary_markdown_file={markdown_path.as_posix()}\n")
            fh.write(f"summary_file={html_path.as_posix()}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["html"])


if __name__ == "__main__":
    main()
