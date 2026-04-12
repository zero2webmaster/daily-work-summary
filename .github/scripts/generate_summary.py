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
SUMMARY_FILE_SUFFIX = "GitHub-Daily-Summary.md"
DEFAULT_REPORT_TIMEZONE = "America/New_York"
TARGET_ORGS_DEFAULT = "zero2webmaster"


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


def _invoke_ai_prompt(prompt: str, max_tokens: int = 220) -> str | None:
    """Run an AI prompt using the configured provider and return text."""
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
            return response.choices[0].message.content.strip()

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()

        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
            )
            return response.text.strip()
    except Exception as e:
        print(f"  AI summary error ({provider}): {e}")
        return None

    return None


def get_report_timezone() -> ZoneInfo:
    """Timezone used for report date and subject date."""
    tz_name = (os.environ.get("EMAIL_TIMEZONE") or DEFAULT_REPORT_TIMEZONE).strip()
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        print(f"  WARNING: invalid EMAIL_TIMEZONE='{tz_name}', falling back to UTC")
        return ZoneInfo("UTC")


def clean_commit_message(msg: str) -> str:
    """Normalize conventional-commit prefixes into human-friendly text."""
    first_line = truncate(msg, length=120)
    cleaned = re.sub(r"^(feat|fix|refactor|chore|docs|test|perf|build|ci|style)(\([^)]+\))?:\s*", "", first_line, flags=re.IGNORECASE)
    return cleaned.strip()


def _fallback_bullet_from_message(msg: str) -> str:
    """Turn a commit message into a conversational accomplishment bullet."""
    text = clean_commit_message(msg)
    if not text:
        return "Moved implementation forward with focused updates."
    text = text.rstrip(".")
    lower = text.lower()

    if lower.startswith(("add ", "added ", "implement ", "implemented ", "create ", "created ", "introduce ", "introduced ")):
        return text[0].upper() + text[1:]
    if lower.startswith(("fix ", "fixed ", "resolve ", "resolved ", "patch ", "patched ")):
        return text[0].upper() + text[1:]
    if lower.startswith(("refactor ", "refactored ", "cleanup ", "cleaned ", "rework ", "reworked ")):
        return text[0].upper() + text[1:]
    if lower.startswith(("update ", "updated ", "improve ", "improved ", "optimize ", "optimized ")):
        return text[0].upper() + text[1:]

    return f"Moved forward on {text}"


def _fallback_repo_bullets(repo_name: str, messages: list[str]) -> list[str]:
    """Build 3-5 bullets without AI."""
    bullets: list[str] = []
    seen: set[str] = set()
    for message in messages:
        candidate = _fallback_bullet_from_message(message)
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        bullets.append(candidate)
        if len(bullets) == 5:
            break

    if len(bullets) < 3:
        bullets.append(
            f"Kept momentum with {len(messages)} commit{'s' if len(messages) != 1 else ''} across {repo_name}."
        )
    if len(bullets) < 3:
        bullets.append("Wrapped the day with iterative polish and follow-through on open items.")

    return bullets[:5]


def _parse_ai_bullets(raw_text: str) -> list[str]:
    """Extract clean bullets from provider output."""
    bullets: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        stripped = re.sub(r"^[-*•\d\.\)\s]+", "", stripped).strip()
        if not stripped:
            continue
        bullets.append(stripped.rstrip(".") + ".")
        if len(bullets) == 5:
            break
    return bullets


def generate_repo_bullets(repo_name: str, messages: list[str]) -> list[str]:
    """Generate 3-5 conversational bullets for a repository."""
    commit_list = "\n".join(f"- {clean_commit_message(m)}" for m in messages[:25])
    prompt = f"""You are writing a daily engineering recap for repository '{repo_name}'.
Based on the commit messages below, produce 3 to 5 short, conversational accomplishment bullets.

Rules:
- Focus on features, bug fixes, refactors, and notable accomplishments.
- Keep each bullet under 130 characters.
- Do not mention commit counts.
- Return bullet lines only.

Commits:
{commit_list}
"""
    ai_text = _invoke_ai_prompt(prompt, max_tokens=260)
    if ai_text:
        ai_bullets = _parse_ai_bullets(ai_text)
        if len(ai_bullets) >= 3:
            return ai_bullets[:5]

    return _fallback_repo_bullets(repo_name, messages)


def list_target_repositories(g: Github, user) -> list:
    """List all personal repos + target organization repos."""
    repos_by_full_name: dict[str, Any] = {}

    # Personal repositories
    for repo in user.get_repos(affiliation="owner"):
        repos_by_full_name[repo.full_name] = repo

    # Organization repositories (defaults to zero2webmaster)
    raw_orgs = os.environ.get("TARGET_GITHUB_ORGS", TARGET_ORGS_DEFAULT)
    org_names = [name.strip() for name in raw_orgs.split(",") if name.strip()]
    for org_name in org_names:
        try:
            org = g.get_organization(org_name)
            for repo in org.get_repos():
                repos_by_full_name[repo.full_name] = repo
        except GithubException as e:
            print(f"  WARNING: could not list repos for org '{org_name}': {e.status}")

    return sorted(repos_by_full_name.values(), key=lambda r: r.full_name.lower())


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
    report_tz = get_report_timezone()
    report_now = datetime.now(report_tz)
    report_date = report_now.strftime("%Y-%m-%d")
    print(f"Fetching commits since: {since.isoformat()}")

    repos = list_target_repositories(g, user)
    print(f"Found {len(repos)} repositories in scope")

    active_repos: list[dict[str, Any]] = []
    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login)
        if not commits:
            continue

        messages = [c.commit.message for c in commits]
        owner, repo_name = repo.full_name.split("/", 1)
        active_repos.append({
            "full_name": repo.full_name,
            "repo_name": repo_name,
            "url": repo.html_url,
            "owner": owner,
            "commits": len(commits),
            "messages": messages,
        })
        print(f"  {repo.full_name}: {len(commits)} commits")

    active_repos.sort(key=lambda r: (-r["commits"], r["full_name"].lower()))

    # No commits — return minimal result
    if not active_repos:
        msg = "No work today - hope you enjoyed the rest!"
        markdown_body = "\n".join(
            [
                f"# Daily Cursor Work - {report_date}",
                "",
                msg,
                "",
                f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
                "",
            ]
        )
        html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
        html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'
        return {
            "html": html,
            "markdown": markdown_body,
            "date": report_date,
            "total_commits": 0,
            "total_repos": 0,
            "repos": [],
            "ai_summaries_text": "",
            "has_commits": False,
        }

    total_commits = sum(repo["commits"] for repo in active_repos)
    total_repos = len(active_repos)

    lines = [
        f"# Daily Cursor Work - {report_date}",
        "",
        "Here is what moved forward in the last 24 hours:",
        "",
        f"**{total_commits} commits** across **{total_repos} active repos**",
        "",
    ]

    ai_summary_lines: list[str] = []
    structured_repos: list[dict[str, Any]] = []

    for repo_data in active_repos:
        repo_name = repo_data["repo_name"]
        messages = repo_data["messages"]
        bullets = generate_repo_bullets(repo_name, messages)

        lines.append(f"**{repo_name}**")
        for bullet in bullets:
            lines.append(f"• {bullet.rstrip('.')}.")
        lines.append("")

        ai_summary_lines.append(f"- {repo_data['full_name']}: {' '.join(bullets[:2])}")
        structured_repos.append({
            "full_name": repo_data["full_name"],
            "url": repo_data["url"],
            "owner": repo_data["owner"],
            "commits": repo_data["commits"],
            "messages": messages,
            "ai_summary": " ".join(bullets),
        })

    lines.append(f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    markdown_body = "\n".join(lines)
    html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
    html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'

    return {
        "html": html,
        "markdown": markdown_body,
        "date": report_date,
        "total_commits": total_commits,
        "total_repos": total_repos,
        "repos": structured_repos,
        "ai_summaries_text": "\n".join(ai_summary_lines),
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

    # Write summary files (always): markdown archive + HTML email body.
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    archive_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-{SUMMARY_FILE_SUFFIX}"
    email_path = Path(SUMMARY_DIR) / f"{summary_data['date']}-Daily-Cursor-Work-Email.html"
    archive_path.write_text(summary_data["markdown"])
    email_path.write_text(summary_data["html"])
    print(f"Summary archive written to: {archive_path}")
    print(f"Email body written to: {email_path}")

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
            fh.write(f"email_file={email_path}\n")
            fh.write(f"subject_date={summary_data['date']}\n")
            fh.write(f"send_email={'true' if send_email else 'false'}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["html"])


if __name__ == "__main__":
    main()
