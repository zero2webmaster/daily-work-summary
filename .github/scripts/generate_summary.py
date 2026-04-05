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
TEMP_DIR = ".tmp"
HTML_FONT_SIZE = "18px"
SUMMARY_FILENAME_TEMPLATE = "{date}-GitHub-Daily-Summary.md"
SUMMARY_HTML_FILENAME_TEMPLATE = "{date}-GitHub-Daily-Summary.html"
NO_WORK_MESSAGE = "No work today - hope you enjoyed the rest!"
AUTH_TOKEN: str | None = None


def get_github_client() -> Github:
    global AUTH_TOKEN
    token = os.environ.get("PAT_GITHUB")
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            token = os.environ.get("PAT_GITHUB")
        except ImportError:
            pass

    if not token:
        try:
            # Cursor cloud runners have gh auth configured even when PAT env vars are absent.
            token = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            token = None

    if not token:
        print("ERROR: PAT_GITHUB not set.")
        print("  GitHub Actions: Add PAT_GITHUB to repository secrets")
        print("  Cursor Cloud:   Ensure gh is authenticated (gh auth status)")
        print("  Local testing:  export PAT_GITHUB=ghp_your_token")
        print("  Create token:   https://github.com/settings/tokens")
        sys.exit(1)

    AUTH_TOKEN = token
    from github import Auth
    return Github(auth=Auth.Token(token), per_page=100)


def list_installation_repositories() -> list[str]:
    """Return full repo names accessible to a GitHub App installation token."""
    if not AUTH_TOKEN:
        return []

    import requests

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    repo_full_names: list[str] = []
    page = 1
    while True:
        url = f"https://api.github.com/installation/repositories?per_page=100&page={page}"
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"  Integration repo listing failed: {response.status_code} {response.text}")
            return repo_full_names

        payload = response.json()
        repos = payload.get("repositories", [])
        for repo in repos:
            full_name = repo.get("full_name")
            if full_name:
                repo_full_names.append(full_name)

        if len(repos) < 100:
            break
        page += 1

    return repo_full_names


def truncate(msg: str, length: int = MAX_MSG_LENGTH) -> str:
    first_line = msg.split("\n")[0].strip()
    if len(first_line) <= length:
        return first_line
    return first_line[: length - 3] + "..."


def normalize_subject(msg: str) -> str:
    """Return a cleaned single-line commit subject."""
    subject = msg.split("\n")[0].strip()
    return re.sub(r"\s+", " ", subject)


def extract_topic(subject: str) -> str:
    """Remove conventional-commit prefixes and return a concise topic phrase."""
    stripped = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    stripped = stripped.strip(".- ")
    if not stripped:
        stripped = subject.strip(".- ")
    if len(stripped) > 70:
        stripped = stripped[:67] + "..."
    return stripped


def categorize_subject(subject: str) -> str:
    """Categorize commit subject into a coarse workstream bucket."""
    s = subject.lower()
    if re.search(r"\b(feat|feature|add|implement|introduce|launch|build)\b", s):
        return "feature"
    if re.search(r"\b(fix|bug|hotfix|patch|resolve|repair)\b", s):
        return "fix"
    if re.search(r"\b(refactor|cleanup|clean up|restructure|simplify|optimi[sz]e)\b", s):
        return "refactor"
    if re.search(r"\b(test|spec|qa|assert)\b", s):
        return "test"
    if re.search(r"\b(docs?|readme|guide|comment)\b", s):
        return "docs"
    if re.search(r"\b(ci|workflow|deploy|release|chore|deps?|dependency|bump)\b", s):
        return "ops"
    return "misc"


def unique_in_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def join_topics(topics: list[str], max_items: int = 2) -> str:
    deduped = unique_in_order(topics)
    if not deduped:
        return "core project areas"
    selected = deduped[:max_items]
    if len(selected) == 1:
        return selected[0]
    if len(selected) == 2:
        return f"{selected[0]} and {selected[1]}"
    return ", ".join(selected[:-1]) + f", and {selected[-1]}"


def build_repo_bullets(messages: list[str], ai_theme: str | None = None) -> list[str]:
    """Create 3-5 conversational bullets summarizing recent repo work."""
    categorized_topics: dict[str, list[str]] = defaultdict(list)
    cleaned_subjects: list[str] = []

    for raw_msg in messages:
        subject = normalize_subject(raw_msg)
        cleaned_subjects.append(subject)
        topic = extract_topic(subject)
        categorized_topics[categorize_subject(subject)].append(topic)

    bullets: list[str] = []
    if ai_theme:
        bullets.append(f"Big picture: {ai_theme.rstrip('.')}.")

    if categorized_topics["feature"]:
        bullets.append(f"Shipped feature work around {join_topics(categorized_topics['feature'])}.")
    if categorized_topics["fix"]:
        bullets.append(f"Closed out bug fixes in {join_topics(categorized_topics['fix'])}.")
    if categorized_topics["refactor"]:
        bullets.append(f"Refactored {join_topics(categorized_topics['refactor'])} to keep things cleaner and easier to maintain.")
    if categorized_topics["test"]:
        bullets.append(f"Improved confidence with test coverage updates around {join_topics(categorized_topics['test'])}.")
    if categorized_topics["docs"]:
        bullets.append(f"Documented and clarified {join_topics(categorized_topics['docs'])} for smoother handoffs.")
    if categorized_topics["ops"]:
        bullets.append(f"Handled operational updates touching {join_topics(categorized_topics['ops'])}.")

    # If we still have fewer than 3 bullets, add concise highlights from raw commit subjects.
    highlights = unique_in_order([extract_topic(s) for s in cleaned_subjects if extract_topic(s)])
    while len(bullets) < 3 and highlights:
        topic = highlights.pop(0)
        bullets.append(f"Advanced {topic} with concrete implementation progress.")

    if len(bullets) < 3:
        bullets.append("Kept steady momentum with focused improvements across the repo.")
    if len(bullets) < 3:
        bullets.append(f"Activity snapshot: {len(messages)} commits landed in the last 24 hours.")

    if len(bullets) < 5:
        bullets.append(f"Total activity: {len(messages)} commits in the last 24 hours.")

    return bullets[:5]


def fetch_commits_with_retry(repo, since, author: str | None, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            if author:
                commits = list(repo.get_commits(since=since, author=author))
            else:
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


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data.

    Returns a dict with keys:
        html, markdown, date, total_commits, total_repos,
        repos (list of dicts), ai_summaries_text, has_commits
    """
    g = get_github_client()
    author_login: str | None = None
    repos = []

    try:
        user = g.get_user()
        author_login = user.login
        repos = list(user.get_repos(affiliation="owner,organization_member"))
        print(f"Authenticated as: {user.login}")
    except GithubException as exc:
        if exc.status != 403:
            raise
        print("Authenticated with GitHub App integration token (installation mode).")
        repo_full_names = list_installation_repositories()
        repos = [g.get_repo(full_name) for full_name in repo_full_names]
        author_login = os.environ.get("SUMMARY_AUTHOR") or os.environ.get("GITHUB_AUTHOR") or os.environ.get("GITHUB_ACTOR")
        if author_login:
            print(f"Filtering commits by author: {author_login}")
        else:
            print("WARNING: No SUMMARY_AUTHOR/GITHUB_AUTHOR/GITHUB_ACTOR set; including all authors in installation repos.")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Fetching commits since: {since.isoformat()}")

    active_repos: list[dict[str, Any]] = []
    print(f"Found {len(repos)} repositories")

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, author_login)
        if commits:
            messages = [c.commit.message for c in commits]
            owner, repo_name = repo.full_name.split("/", 1)
            active_repos.append({
                "full_name": repo.full_name,
                "url": repo.html_url,
                "owner": owner,
                "repo_name": repo_name,
                "messages": messages,
                "commits": len(messages),
            })
            print(f"  {repo.full_name}: {len(commits)} commits")

    # No commits — return minimal result
    if not active_repos:
        msg = NO_WORK_MESSAGE
        markdown_body = "\n".join([
            f"# Daily Cursor Work - {today}",
            "",
            msg,
            "",
            f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
        ])
        html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
        footer = (
            "<p>Daily Work Summary initially created by "
            '<a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>'
            '<p>Contribute to the public repository at: '
            '<a href="https://github.com/zero2webmaster/daily-work-summary">github.com/zero2webmaster/daily-work-summary</a></p>'
        )
        html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}{footer}</div>'
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
    total_commits = sum(r["commits"] for r in active_repos)
    total_repos = len(active_repos)

    lines = [
        f"# Daily Cursor Work - {datetime.now(timezone.utc).strftime('%a %b %d, %Y')}",
        "",
        f"Reviewed **{total_commits} commits** across **{total_repos} active repos**.",
        "",
        "---",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []

    for repo_info in active_repos:
        repo_name = repo_info["repo_name"]
        full_name = repo_info["full_name"]
        count = repo_info["commits"]
        messages = repo_info["messages"]

        ai_summary = generate_ai_repo_summary(messages)
        bullets = build_repo_bullets(messages, ai_summary=ai_summary)
        lines.append(f"**{repo_name}**")
        lines.append(f"_[{full_name}]({repo_info['url']}) · {count} commit{'s' if count != 1 else ''}_")
        for bullet in bullets:
            lines.append(f"• {bullet}")
        lines.append("")

        if ai_summary:
            ai_summary_bullets.append(f"- {repo_name}: {ai_summary}")

        structured_repos.append({
            "full_name": full_name,
            "url": repo_info["url"],
            "owner": repo_info["owner"],
            "commits": count,
            "messages": messages,
            "ai_summary": ai_summary,
            "bullets": bullets,
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

    # Write summary files:
    # - markdown archive (committed)
    # - html body (used by email step)
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    Path(TEMP_DIR).mkdir(exist_ok=True)
    summary_path = Path(SUMMARY_DIR) / SUMMARY_FILENAME_TEMPLATE.format(date=summary_data["date"])
    summary_html_path = Path(TEMP_DIR) / SUMMARY_HTML_FILENAME_TEMPLATE.format(date=summary_data["date"])
    summary_path.write_text(summary_data["markdown"], encoding="utf-8")
    summary_html_path.write_text(summary_data["html"], encoding="utf-8")
    print(f"Markdown summary written to: {summary_path}")
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
            fh.write(f"summary_file={summary_path}\n")
            fh.write(f"summary_html_file={summary_html_path}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
