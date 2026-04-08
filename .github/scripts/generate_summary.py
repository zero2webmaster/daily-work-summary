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
import subprocess
import sys
import time
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
TARGET_ORG = "zero2webmaster"
NO_WORK_MESSAGE = "No work today - hope you enjoyed the rest!"
MIN_REPO_BULLETS = 3
MAX_REPO_BULLETS = 5


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


def fetch_commits_with_retry(repo, since, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            commits = list(repo.get_commits(since=since))
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


def get_run_timezone() -> ZoneInfo:
    tz_name = (os.environ.get("EMAIL_TIMEZONE") or "America/New_York").strip()
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        print(f"  WARNING: Unknown EMAIL_TIMEZONE '{tz_name}', defaulting to UTC")
        return ZoneInfo("UTC")


def get_target_repositories(g: Github, user_login: str) -> list[Any]:
    """Return personal repos plus all repos from zero2webmaster org."""
    repos_by_name: dict[str, Any] = {}
    user = g.get_user()

    # Personal repositories owned by the authenticated user.
    for repo in user.get_repos(type="owner"):
        repos_by_name[repo.full_name] = repo

    # zero2webmaster organization repositories.
    try:
        org = g.get_organization(TARGET_ORG)
        for repo in org.get_repos(type="all"):
            repos_by_name[repo.full_name] = repo
    except GithubException as exc:
        print(f"  WARNING: Could not load org repos for '{TARGET_ORG}': {exc.status}")

    repos = sorted(repos_by_name.values(), key=lambda r: r.full_name.lower())
    print(f"Found {len(repos)} target repositories ({user_login} + {TARGET_ORG})")
    return repos


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


def _extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = stripped.lstrip("-*•0123456789. )(").strip()
        if cleaned and cleaned not in seen:
            bullets.append(cleaned)
            seen.add(cleaned)
        if len(bullets) >= MAX_REPO_BULLETS:
            break
    return bullets


def _fallback_repo_bullets(messages: list[str], commit_count: int) -> list[str]:
    bullets: list[str] = []
    if commit_count == 1:
        bullets.append("Shipped one meaningful update in this project over the last 24 hours.")
    else:
        bullets.append(f"Shipped {commit_count} commits in this project over the last 24 hours.")

    seen: set[str] = set()
    for msg in messages:
        text = truncate(msg)
        if text and text not in seen:
            bullets.append(text)
            seen.add(text)
        if len(bullets) >= MAX_REPO_BULLETS:
            break

    while len(bullets) < MIN_REPO_BULLETS:
        bullets.append("Progress stayed focused on steady feature delivery and maintenance.")
    return bullets[:MAX_REPO_BULLETS]


def generate_ai_repo_bullets(messages: list[str]) -> list[str] | None:
    """Generate 3-5 summary bullets from commit messages."""
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        print("  AI summary: skipped (no provider key configured)")
        return None
    print(f"  AI summary: using {provider}/{model}")

    commit_list = "\n".join(truncate(m) for m in messages[:20])
    prompt = f"""Turn these git commits into 3-5 concise project update bullets.

Rules:
- Return plain bullet lines only (no intro/outro)
- Keep each bullet under 120 characters
- Use conversational, accomplishment-oriented wording
- Group related commit messages into themes (features, fixes, refactors, outcomes)
- Do not mention exact commit counts

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

        bullets = _extract_bullets(summary_text)
        if bullets:
            while len(bullets) < MIN_REPO_BULLETS:
                bullets.append("Kept shipping focused improvements and maintenance updates.")
            return bullets[:MAX_REPO_BULLETS]
        return None
    except Exception as e:
        print(f"  AI summary error ({provider}): {e}")
        return None


def build_repo_bullets(messages: list[str], commit_count: int) -> list[str]:
    ai_bullets = generate_ai_repo_bullets(messages)
    if ai_bullets:
        return ai_bullets[:MAX_REPO_BULLETS]
    return _fallback_repo_bullets(messages, commit_count)


def build_summary_payload(
    structured_repos: list[dict[str, Any]],
    today: str,
    display_date: str,
    now_utc: datetime,
) -> dict[str, Any]:
    """Build markdown/html payload from structured repo data."""
    if not structured_repos:
        markdown_body = f"# Daily Cursor Work - {display_date}\n\n{NO_WORK_MESSAGE}\n"
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

    structured_repos = sorted(
        structured_repos,
        key=lambda r: (-r["commits"], r["full_name"].lower()),
    )
    total_commits = sum(repo["commits"] for repo in structured_repos)
    total_repos = len(structured_repos)

    lines = [
        f"# Daily Cursor Work - {display_date}",
        "",
        "Quick pulse from the last 24 hours across your personal and zero2webmaster repos.",
        "",
        f"**{total_commits} commits** across **{total_repos} active repos**.",
        "",
    ]

    ai_summary_bullets: list[str] = []

    for repo in structured_repos:
        repo_name = repo["repo_name"]
        lines.append(f"**{repo_name}**")
        lines.append("")
        for bullet in repo["bullets"][:MAX_REPO_BULLETS]:
            lines.append(f"• {bullet}")
        lines.append("")
        if repo["bullets"]:
            ai_summary_bullets.append(f"- {repo_name}: {repo['bullets'][0]}")

    lines.append(f"*Generated at {now_utc.strftime('%Y-%m-%d %H:%M UTC')}*")

    markdown_body = "\n".join(lines).strip() + "\n"
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


def _run_gh_api_json(args: list[str]) -> Any:
    cmd = ["gh", "api", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh api call failed")
    return json.loads(result.stdout)


def generate_summary_via_gh_integration() -> dict[str, Any]:
    """Fallback mode when PAT_GITHUB is unavailable in this environment."""
    print("PAT_GITHUB unavailable/insufficient; falling back to GitHub integration token via gh CLI.")
    now_utc = datetime.now(timezone.utc)
    since = now_utc - timedelta(hours=24)
    tz = get_run_timezone()
    today = now_utc.astimezone(tz).strftime("%Y-%m-%d")
    display_date = now_utc.astimezone(tz).strftime("%a %b %d, %Y")

    installation = _run_gh_api_json(["/installation/repositories"])
    repos = installation.get("repositories", [])
    print(f"Integration has access to {len(repos)} repositories.")

    structured_repos: list[dict[str, Any]] = []
    for repo in repos:
        if repo.get("archived"):
            continue
        full_name = repo.get("full_name")
        if not full_name:
            continue
        owner, repo_name = full_name.split("/", 1)

        try:
            commits = _run_gh_api_json(
                [
                    f"/repos/{full_name}/commits",
                    "-f",
                    f"since={since.isoformat()}",
                    "-f",
                    "per_page=100",
                ]
            )
        except Exception as exc:
            print(f"  Warning: failed to fetch commits for {full_name}: {exc}")
            continue

        if not isinstance(commits, list) or not commits:
            continue

        messages = []
        for commit in commits:
            msg = commit.get("commit", {}).get("message")
            if msg:
                messages.append(msg)
        if not messages:
            continue

        count = len(messages)
        bullets = build_repo_bullets(messages, count)
        structured_repos.append({
            "full_name": full_name,
            "url": repo.get("html_url", f"https://github.com/{full_name}"),
            "owner": owner,
            "repo_name": repo_name,
            "commits": count,
            "messages": messages,
            "bullets": bullets,
            "ai_summary": bullets[0] if bullets else None,
        })
        print(f"  {full_name}: {count} commits")

    return build_summary_payload(structured_repos, today, display_date, now_utc)


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data.

    Returns a dict with keys:
        html, markdown, date, total_commits, total_repos,
        repos (list of dicts), ai_summaries_text, has_commits
    """
    g = get_github_client()
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    now_utc = datetime.now(timezone.utc)
    since = now_utc - timedelta(hours=24)
    tz = get_run_timezone()
    today = now_utc.astimezone(tz).strftime("%Y-%m-%d")
    display_date = now_utc.astimezone(tz).strftime("%a %b %d, %Y")
    print(f"Fetching commits since: {since.isoformat()}")

    repos = get_target_repositories(g, user.login)
    structured_repos: list[dict[str, Any]] = []

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since)
        if commits:
            messages = [c.commit.message for c in commits]
            print(f"  {repo.full_name}: {len(commits)} commits")
            owner, repo_name = repo.full_name.split("/", 1)
            count = len(commits)
            bullets = build_repo_bullets(messages, count)
            structured_repos.append({
                "full_name": repo.full_name,
                "url": repo.html_url,
                "owner": owner,
                "repo_name": repo_name,
                "commits": count,
                "messages": messages,
                "bullets": bullets,
                "ai_summary": bullets[0] if bullets else None,
            })

    return build_summary_payload(structured_repos, today, display_date, now_utc)


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

    summary_data: dict[str, Any]
    try:
        summary_data = generate_summary()
    except SystemExit:
        # Local/automation environments may not provide PAT_GITHUB.
        summary_data = generate_summary_via_gh_integration()
    except GithubException as e:
        if e.status in (401, 403):
            print("Primary PAT flow unavailable; trying gh integration fallback...")
            try:
                summary_data = generate_summary_via_gh_integration()
            except Exception:
                if e.status == 401:
                    print("ERROR: PAT_GITHUB is invalid or expired.")
                    print("  Regenerate at: https://github.com/settings/tokens")
                else:
                    print("ERROR: PAT_GITHUB has insufficient permissions.")
                    print("  Required scopes: repo, read:user")
                    print("  Update at: https://github.com/settings/tokens")
                sys.exit(1)
        else:
            raise

    # Determine delivery methods (comma-separated, 'both' = email+airtable)
    delivery_methods = parse_delivery_methods(os.environ.get("DELIVERY_METHOD"))
    print(f"\nDelivery methods: {', '.join(sorted(delivery_methods))}")

    # Write archive markdown and email HTML files.
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    archive_path = Path(f"{summary_data['date']}-GitHub-Daily-Summary.md")
    email_html_path = Path(SUMMARY_DIR) / f"daily-summary-email-{summary_data['date']}.html"
    archive_path.write_text(summary_data["markdown"], encoding="utf-8")
    email_html_path.write_text(summary_data["html"], encoding="utf-8")
    print(f"Summary archive written to: {archive_path}")
    print(f"Email HTML written to: {email_html_path}")

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
            fh.write("has_summary=true\n")
            fh.write(f"summary_file={archive_path}\n")
            fh.write(f"email_html_file={email_html_path}\n")
            fh.write(f"send_email={'true' if send_email else 'false'}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
