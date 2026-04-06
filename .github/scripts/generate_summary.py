#!/usr/bin/env python3
"""
Daily Work Summary Generator

Fetches all commits from the last 24 hours across every repository
the authenticated GitHub user owns, then generates a smart grouped
summary as Markdown with optional AI-powered repo descriptions.

Supports multiple delivery methods controlled by the DELIVERY_METHOD
environment variable (comma-separated list):
  email    — send email via Gmail SMTP (local/Cursor) or workflow step (Actions)
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
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
SUMMARY_FILE_TEMPLATE = "{date}-GitHub-Daily-Summary.md"
HTML_FONT_SIZE = "18px"
NO_WORK_MESSAGE = "No work today – hope you enjoyed the rest!"


def get_email_timezone() -> ZoneInfo:
    tz_name = os.environ.get("EMAIL_TIMEZONE", "America/New_York")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        print(f"WARNING: Invalid EMAIL_TIMEZONE '{tz_name}', falling back to UTC")
        return ZoneInfo("UTC")


def get_local_now() -> datetime:
    return datetime.now(get_email_timezone())


def get_local_date_iso() -> str:
    return get_local_now().strftime("%Y-%m-%d")


def get_local_date_display() -> str:
    return get_local_now().strftime("%a %b %d, %Y")


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


def get_fallback_login_from_gh_cli() -> str | None:
    """Best-effort parse of active gh account login."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    match = re.search(r"Logged in to github\.com account\s+([^\s(]+)", result.stdout)
    if match:
        return match.group(1).strip()
    return None


def get_repos_for_owner(g: Github, owner: str):
    """Return repos for a user/org owner name. Returns [] on access errors."""
    try:
        return list(g.get_organization(owner).get_repos())
    except GithubException:
        pass
    except Exception:
        pass

    try:
        return list(g.get_user(owner).get_repos())
    except Exception as exc:
        print(f"  WARNING: Could not list repos for owner '{owner}': {exc}")
        return []


def truncate(msg: str, length: int = MAX_MSG_LENGTH) -> str:
    first_line = msg.split("\n")[0].strip()
    if len(first_line) <= length:
        return first_line
    return first_line[: length - 3] + "..."


def fetch_commits_with_retry(repo, since, author: str | None, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            params = {"since": since}
            if author:
                params["author"] = author
            commits = list(repo.get_commits(**params))
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


def _normalize_message(msg: str) -> str:
    first_line = msg.split("\n", 1)[0].strip()
    first_line = re.sub(r"^\s*[-*•]+\s*", "", first_line)
    return truncate(first_line)


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def _parse_bullet_lines(raw_text: str) -> list[str]:
    bullets: list[str] = []
    for line in raw_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", cleaned)
        cleaned = cleaned.strip(" \t-•*")
        if cleaned:
            bullets.append(cleaned.rstrip("."))
    return _dedupe_keep_order(bullets)


def _fallback_repo_bullets(messages: list[str]) -> list[str]:
    type_prefix = {
        "feat": "Shipped",
        "fix": "Fixed",
        "refactor": "Refactored",
        "docs": "Documented",
        "doc": "Documented",
        "chore": "Improved",
        "test": "Strengthened tests around",
        "perf": "Improved performance for",
        "ci": "Updated CI for",
        "build": "Updated build workflow for",
    }

    normalized = _dedupe_keep_order([_normalize_message(m) for m in messages])
    bullets: list[str] = []
    conventional_pattern = re.compile(
        r"^(feat|fix|refactor|docs?|chore|test|perf|ci|build)(?:\([^)]+\))?!?:\s*(.+)$",
        re.IGNORECASE,
    )

    for msg in normalized:
        match = conventional_pattern.match(msg)
        if match:
            commit_type = match.group(1).lower()
            body = match.group(2).strip()
            prefix = type_prefix.get(commit_type, "Updated")
            bullets.append(f"{prefix} {body}".rstrip("."))
        else:
            bullets.append(msg.rstrip("."))

    bullets = _dedupe_keep_order(bullets)[:5]
    fallback_fillers = [
        "Polished edge-case handling and implementation details",
        "Wrapped up quality-of-life cleanup to improve maintainability",
        "Kept project momentum with targeted follow-up refinements",
    ]
    for filler in fallback_fillers:
        if len(bullets) >= 3:
            break
        bullets.append(filler)

    return bullets[:5]


def generate_repo_bullets(repo_name: str, messages: list[str]) -> list[str]:
    """Generate 3-5 conversational bullets describing work in one repo."""
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        return _fallback_repo_bullets(messages)

    print(f"  AI bullets: using {provider}/{model}")
    commit_list = "\n".join(_normalize_message(m) for m in messages[:30])
    prompt = f"""Write a concise daily engineering update for the repository "{repo_name}".

Return ONLY 3 to 5 bullet points, one per line.
Each line must start with "• " and be conversational, specific, and impact-focused.

Rules:
- Focus on features, refactors, bug fixes, and accomplishments
- Do not mention commit counts, SHAs, PR numbers, or branch names
- Keep each bullet under 140 characters
- Do not add a heading, intro, or outro

Commit messages:
{commit_list}
"""

    try:
        if provider == "openrouter":
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
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
            return _fallback_repo_bullets(messages)

        bullets = _parse_bullet_lines(summary_text)
        if len(bullets) < 3:
            return _fallback_repo_bullets(messages)
        return bullets[:5]

    except Exception as exc:
        print(f"  AI bullets error ({provider}): {exc}")
        return _fallback_repo_bullets(messages)


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data.

    Returns a dict with keys:
        html, markdown, date, total_commits, total_repos,
        repos (list of dicts), ai_summaries_text, has_commits
    """
    g = get_github_client()
    repos = []
    commit_author: str | None = None
    commit_author_override = (os.environ.get("GITHUB_COMMIT_AUTHOR") or "").strip()
    include_all_authors = commit_author_override.lower() in {"all", "any", "*"}

    try:
        user = g.get_user()
        commit_author = None if include_all_authors else user.login
        if commit_author:
            print(f"Authenticated as: {commit_author}")
        else:
            print("Authenticated token ready (including commits from all authors)")
        repos = list(user.get_repos(affiliation="owner,organization_member"))
    except GithubException as exc:
        if exc.status != 403:
            raise

        print("WARNING: Token cannot read /user endpoint; using owner-based fallback mode.")
        fallback_login = get_fallback_login_from_gh_cli()
        if not fallback_login and not include_all_authors and not commit_author_override:
            print("ERROR: Could not determine commit author login for fallback mode.")
            sys.exit(1)

        if include_all_authors:
            commit_author = None
        elif commit_author_override:
            commit_author = commit_author_override
        else:
            commit_author = fallback_login

        owner_fallback = fallback_login or "zero2webmaster"
        owners_env = os.environ.get("GITHUB_SUMMARY_OWNERS", "").strip()
        if owners_env:
            owners = [o.strip() for o in owners_env.split(",") if o.strip()]
        else:
            owners = ["zero2webmaster", owner_fallback]
        owners = list(dict.fromkeys(owners))  # preserve order, remove duplicates

        print(f"Fallback owners: {', '.join(owners)}")
        for owner in owners:
            repos.extend(get_repos_for_owner(g, owner))

    # De-duplicate repos by owner/name
    unique_repos = {repo.full_name: repo for repo in repos}
    repos = list(unique_repos.values())

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    today = get_local_date_iso()
    today_display = get_local_date_display()
    print(f"Fetching commits since: {since.isoformat()}")

    active_repos: list[dict[str, Any]] = []
    print(f"Found {len(repos)} repositories")
    if commit_author:
        print(f"Filtering commits by author: {commit_author}")
    else:
        print("Filtering commits by author: all authors")

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, commit_author)
        if commits:
            messages = [c.commit.message for c in commits]
            owner, repo_name = repo.full_name.split("/", 1)
            active_repos.append({
                "full_name": repo.full_name,
                "repo_name": repo_name,
                "owner": owner,
                "url": repo.html_url,
                "messages": messages,
                "commits": len(commits),
            })
            print(f"  {repo.full_name}: {len(commits)} commits")

    # No commits — return minimal result
    if not active_repos:
        footer = (
            "<p>Daily Cursor Work summary by "
            '<a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>'
            '<p>Project repo: <a href="https://github.com/zero2webmaster/daily-work-summary">'
            "github.com/zero2webmaster/daily-work-summary</a></p>"
        )
        html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;"><p>{NO_WORK_MESSAGE}</p>{footer}</div>'
        return {
            "html": html,
            "markdown": NO_WORK_MESSAGE,
            "date": today,
            "date_display": today_display,
            "total_commits": 0,
            "total_repos": 0,
            "repos": [],
            "ai_summaries_text": "",
            "has_commits": False,
        }

    active_repos.sort(key=lambda r: (-r["commits"], r["full_name"].lower()))
    total_commits = sum(r["commits"] for r in active_repos)
    total_repos = len(active_repos)

    total_commit_label = f"{total_commits} commit{'s' if total_commits != 1 else ''}"
    total_repo_label = f"{total_repos} active repo{'s' if total_repos != 1 else ''}"

    lines = [
        f"# Daily Cursor Work - {today_display}",
        "",
        f"Here’s what moved in the last 24 hours: **{total_commit_label}** across **{total_repo_label}**.",
        "",
        "---",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []

    for repo in active_repos:
        full_name = repo["full_name"]
        repo_name = repo["repo_name"]
        count = repo["commits"]
        messages = repo["messages"]
        commit_label = f"{count} commit{'s' if count != 1 else ''}"
        repo_bullets = generate_repo_bullets(repo_name, messages)

        lines.append(f"**[{full_name}]({repo['url']})** ({commit_label})")
        for bullet in repo_bullets:
            lines.append(f"• {bullet}")
        lines.append("")

        ai_summary_bullets.append(f"- {full_name}: {'; '.join(repo_bullets)}")
        structured_repos.append({
            "full_name": full_name,
            "url": repo["url"],
            "owner": repo["owner"],
            "commits": count,
            "messages": messages,
            "summary_bullets": repo_bullets,
            # Backward-compatible single summary for Slack/Discord/Airtable consumers.
            "ai_summary": repo_bullets[0] if repo_bullets else None,
        })

    lines.append("---")
    lines.append("")
    lines.append("Daily Cursor Work summary by [Zero2Webmaster Founder Dr. Kerry Kriger](https://zero2webmaster.com/kerry-kriger)")
    lines.append("")
    lines.append("Project repo: https://github.com/zero2webmaster/daily-work-summary")
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
        "date_display": today_display,
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
# Email delivery (local runtime)
# ------------------------------------------------------------------

def send_email_via_smtp(summary_data: dict[str, Any], summary_path: Path) -> bool:
    """Send the summary directly via Gmail SMTP when running outside Actions."""
    username = os.environ.get("EMAIL_USERNAME")
    password = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_TO", "kerry@zero2webmaster.com")

    if not username or not password:
        print("  Email: missing EMAIL_USERNAME or EMAIL_PASSWORD")
        return False

    subject = f"Daily Cursor Work - {summary_data['date']}"
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = username
    message["To"] = recipient

    plain_body = summary_path.read_text()
    html_body = summary_data["html"]
    message.attach(MIMEText(plain_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(username, password)
            server.sendmail(username, [recipient], message.as_string())
        print(f"  Email: sent to {recipient}")
        return True
    except Exception as exc:
        print(f"  Email ERROR: {exc}")
        return False


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

    # Write summary archive (always)
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    summary_filename = SUMMARY_FILE_TEMPLATE.format(date=summary_data["date"])
    summary_path = Path(SUMMARY_DIR) / summary_filename
    summary_path.write_text(summary_data["markdown"])
    print(f"Summary written to: {summary_path}")

    running_in_actions = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"

    # Email delivery:
    # - In GitHub Actions: workflow handles it via action-send-mail.
    # - In local/Cursor automation: send directly via SMTP.
    email_requested = "email" in delivery_methods
    email_sent_locally = False
    if email_requested and not running_in_actions:
        print("\n--- Email Delivery ---")
        email_sent_locally = send_email_via_smtp(summary_data, summary_path)
        if not email_sent_locally:
            print("ERROR: Email delivery requested but failed.")
            sys.exit(1)
    elif email_requested:
        print("\n  Email: delegated to workflow send-mail step")

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

    # Tell the workflow whether to run the email step (Actions only)
    send_email_for_workflow = email_requested and running_in_actions
    if not email_requested:
        active = ", ".join(sorted(delivery_methods - {"email"}))
        print(f"\n  Email step: skipped (delivery is {active} only)")

    # Write outputs for the workflow to consume
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"send_email={'true' if send_email_for_workflow else 'false'}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
