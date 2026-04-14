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

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

MAX_MSG_LENGTH = 80
MAX_RETRIES = 3
SUMMARY_DIR = "summaries"
EMAIL_PREVIEW_DIR = ".tmp"
HTML_FONT_SIZE = "18px"
NO_WORK_MESSAGE = "No work today - hope you enjoyed the rest!"
GITHUB_API_BASE = "https://api.github.com"


def get_github_token() -> str:
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
            token = subprocess.check_output(
                ["gh", "auth", "token"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            token = None

    if not token:
        print("ERROR: PAT_GITHUB not set.")
        print("  GitHub Actions: Add PAT_GITHUB to repository secrets")
        print("  Local testing:  export PAT_GITHUB=ghp_your_token")
        print("  Create token:   https://github.com/settings/tokens")
        sys.exit(1)

    return token


def get_github_client(token: str) -> Github:
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


def _safe_json(response: "requests.Response") -> Any:
    try:
        return response.json()
    except ValueError:
        return {}


def collect_repos_via_installation_api(token: str) -> list[dict[str, Any]]:
    """Collect repositories available to a GitHub App installation token."""
    repos: list[dict[str, Any]] = []
    page = 1
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    while True:
        resp = requests.get(
            f"{GITHUB_API_BASE}/installation/repositories",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=20,
        )
        if resp.status_code >= 400:
            data = _safe_json(resp)
            message = data.get("message", "Unknown error")
            raise RuntimeError(
                f"Installation repo listing failed (HTTP {resp.status_code}): {message}"
            )

        payload = _safe_json(resp)
        repo_batch = payload.get("repositories", [])
        repos.extend(repo_batch)
        if len(repo_batch) < 100:
            break
        page += 1
    return repos


def fetch_commits_via_rest_with_retry(
    token: str,
    repo_full_name: str,
    since: datetime,
    author_login: str | None,
    retries: int = MAX_RETRIES,
) -> list[str]:
    """Fetch commit messages via REST API for integration-token fallback."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    since_iso = since.isoformat()
    messages: list[str] = []

    for attempt in range(retries):
        try:
            page = 1
            messages.clear()
            while True:
                resp = requests.get(
                    f"{GITHUB_API_BASE}/repos/{repo_full_name}/commits",
                    headers=headers,
                    params={"since": since_iso, "per_page": 100, "page": page},
                    timeout=25,
                )
                if resp.status_code == 409:
                    return []
                if resp.status_code == 403 and attempt < retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  403 error on {repo_full_name}, retrying in {wait}s...")
                    time.sleep(wait)
                    break
                if resp.status_code >= 400:
                    data = _safe_json(resp)
                    message = data.get("message", "Unknown error")
                    print(f"  Error fetching {repo_full_name}: HTTP {resp.status_code} {message}")
                    return []

                commits = _safe_json(resp)
                if not isinstance(commits, list):
                    return []

                for commit in commits:
                    commit_author = (commit.get("author") or {}).get("login")
                    if author_login and commit_author != author_login:
                        continue
                    msg = ((commit.get("commit") or {}).get("message") or "").strip()
                    if msg:
                        messages.append(msg)

                if len(commits) < 100:
                    return messages
                page += 1
            else:
                return messages
        except requests.RequestException as exc:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Network error on {repo_full_name} ({exc}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Failed fetching {repo_full_name} after {retries} retries: {exc}")
                return []

    return messages


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


def _generate_ai_text(prompt: str, max_tokens: int = 220) -> str | None:
    """Generate text from the configured AI provider."""
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        print("  AI summary: skipped (no provider key configured)")
        return None
    print(f"  AI summary: using {provider}/{model}")

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
                max_tokens=max_tokens,
            )
            summary = response.choices[0].message.content.strip()

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            summary = response.choices[0].message.content.strip()

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            summary = response.content[0].text.strip()

        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
            )
            summary = response.text.strip()

        else:
            return None

        return summary.strip()
    except Exception as e:
        print(f"  AI summary error ({provider}): {e}")
        return None


def get_report_date() -> tuple[datetime, str]:
    """Return (now_in_report_tz, YYYY-MM-DD)."""
    timezone_name = os.environ.get("EMAIL_TIMEZONE") or "America/New_York"
    try:
        now_local = datetime.now(ZoneInfo(timezone_name))
    except Exception:
        print(f"  WARNING: invalid EMAIL_TIMEZONE='{timezone_name}', using America/New_York")
        now_local = datetime.now(ZoneInfo("America/New_York"))
    return now_local, now_local.strftime("%Y-%m-%d")


def _normalize_bullets(raw_text: str) -> list[str]:
    """Normalize AI bullet text into plain bullet lines."""
    bullets: list[str] = []
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        stripped = re.sub(r"^\d+[\).\s-]*", "", stripped)
        stripped = re.sub(r"^[\-*•]+\s*", "", stripped)
        stripped = stripped.strip().rstrip(".")
        if stripped:
            bullets.append(stripped)
    return bullets


def _fallback_repo_bullets(messages: list[str]) -> list[str]:
    """Deterministic fallback bullets when AI is unavailable."""
    first_lines: list[str] = []
    seen = set()
    for msg in messages:
        first = truncate(msg)
        lower = first.lower()
        if lower in seen:
            continue
        seen.add(lower)
        first_lines.append(first)
        if len(first_lines) == 5:
            break

    if not first_lines:
        return []

    bullets = first_lines[:]
    if len(bullets) < 3:
        commit_count = len(messages)
        bullets.insert(0, f"Moved {commit_count} commit{'s' if commit_count != 1 else ''} forward in this project")
    return bullets[:5]


def generate_repo_bullets(repo_full_name: str, messages: list[str]) -> list[str]:
    """Return 3-5 accomplishment bullets for a repository when possible."""
    commit_list = "\n".join(f"- {truncate(m)}" for m in messages[:30])
    prompt = f"""You are summarizing daily git activity for one repository.

Repository: {repo_full_name}

Produce 3-5 concise bullets in a conversational but professional tone.
Each bullet must describe accomplishments (features, refactors, bug fixes, or improvements).
Do not mention commit counts. Do not invent work. Use only the commit messages below.
Start each line with a bullet marker.

Commit messages:
{commit_list}
"""

    ai_text = _generate_ai_text(prompt, max_tokens=220)
    if not ai_text:
        return _fallback_repo_bullets(messages)

    bullets = _normalize_bullets(ai_text)
    if len(bullets) < 2:
        return _fallback_repo_bullets(messages)

    return bullets[:5]


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data.

    Returns a dict with keys:
        html, markdown, date, total_commits, total_repos,
        repos (list of dicts), ai_summaries_text, has_commits
    """
    token = get_github_token()
    g = get_github_client(token)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    report_now_local, today = get_report_date()
    print(f"Fetching commits since: {since.isoformat()}")

    repo_summaries: list[dict[str, Any]] = []
    allow_installation_fallback = (
        os.environ.get("ALLOW_INTEGRATION_INSTALLATION_FALLBACK", "").lower() == "true"
    )

    repos_data: list[dict[str, Any]] = []
    author_login: str | None = None
    using_installation_fallback = False
    try:
        user = g.get_user()
        author_login = user.login
        print(f"Authenticated as: {user.login}")
        repos = list(user.get_repos(affiliation="owner,organization_member"))
        print(f"Found {len(repos)} repositories")
        for repo in repos:
            repos_data.append({
                "full_name": repo.full_name,
                "repo_name": repo.name,
                "url": repo.html_url,
                "owner": repo.owner.login,
                "archived": bool(repo.archived),
                "repo_obj": repo,
            })
    except GithubException as exc:
        if exc.status != 403 or not allow_installation_fallback:
            raise
        print("GitHub token cannot access /user endpoint; using installation repository fallback")
        using_installation_fallback = True
        repos = collect_repos_via_installation_api(token)
        print(f"Found {len(repos)} installation repositories")
        author_login = (os.environ.get("SUMMARY_AUTHOR_LOGIN") or "").strip() or None
        for repo in repos:
            full_name = repo.get("full_name")
            if not full_name:
                continue
            owner, repo_name = full_name.split("/", 1)
            repos_data.append({
                "full_name": full_name,
                "repo_name": repo_name,
                "url": repo.get("html_url", f"https://github.com/{full_name}"),
                "owner": owner,
                "archived": bool(repo.get("archived")),
            })

    for repo_data in repos_data:
        if repo_data.get("archived"):
            continue

        if using_installation_fallback:
            messages = fetch_commits_via_rest_with_retry(
                token=token,
                repo_full_name=repo_data["full_name"],
                since=since,
                author_login=author_login,
            )
        else:
            commits = fetch_commits_with_retry(repo_data["repo_obj"], since, author_login)
            messages = [c.commit.message for c in commits]

        if not messages:
            continue

        repo_summaries.append({
            "full_name": repo_data["full_name"],
            "repo_name": repo_data["repo_name"],
            "url": repo_data["url"],
            "owner": repo_data["owner"],
            "commits": len(messages),
            "messages": messages,
        })
        print(f"  {repo_data['full_name']}: {len(messages)} commits")

    # No commits — return minimal result
    if not repo_summaries:
        lines = [
            f"# Daily Cursor Work - {today}",
            "",
            NO_WORK_MESSAGE,
            "",
            "_Checked all repositories for the last 24 hours._",
            "",
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

    sorted_repos = sorted(
        repo_summaries,
        key=lambda r: (-r["commits"], r["full_name"].lower()),
    )
    total_commits = sum(r["commits"] for r in sorted_repos)
    total_repos = len(sorted_repos)

    lines = [
        f"# Daily Cursor Work - {today}",
        "",
        "Quick update from your last 24 hours on GitHub:",
        "",
        f"**{total_commits} commits** across **{total_repos} active repos**",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []

    for repo_data in sorted_repos:
        full_name = repo_data["full_name"]
        repo_name = repo_data["repo_name"]
        count = repo_data["commits"]
        messages = repo_data["messages"]
        owner = repo_data["owner"]
        accomplishment_bullets = generate_repo_bullets(full_name, messages)
        ai_summary = accomplishment_bullets[0] if accomplishment_bullets else None

        lines.append(f"**{repo_name}** ({count} commit{'s' if count != 1 else ''})")
        for bullet in accomplishment_bullets:
            lines.append(f"• {bullet}")
        lines.append("")

        if accomplishment_bullets:
            compact = "; ".join(accomplishment_bullets[:3])
            ai_summary_bullets.append(f"- {full_name}: {compact}")

        structured_repos.append({
            "full_name": full_name,
            "url": repo_data["url"],
            "owner": owner,
            "commits": count,
            "messages": messages,
            "summary_bullets": accomplishment_bullets,
            "ai_summary": ai_summary,
        })

    lines.append(f"*Generated {report_now_local.strftime('%Y-%m-%d %H:%M %Z')}*")
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

    # Write markdown archive + HTML email body.
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    Path(EMAIL_PREVIEW_DIR).mkdir(exist_ok=True)

    archive_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.md"
    archive_path.write_text(summary_data["markdown"], encoding="utf-8")
    print(f"Archive written to: {archive_path}")

    html_path = Path(EMAIL_PREVIEW_DIR) / f"{summary_data['date']}-GitHub-Daily-Summary.html"
    html_path.write_text(summary_data["html"], encoding="utf-8")
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
            fh.write(f"send_email={'true' if send_email else 'false'}\n")
            fh.write("has_summary=true\n")
            fh.write(f"summary_file={html_path}\n")
            fh.write(f"archive_file={archive_path}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["html"])


if __name__ == "__main__":
    main()
