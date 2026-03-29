#!/usr/bin/env python3
"""
Daily Cursor Work Summary generator.

Primary mode:
  - Uses PAT_GITHUB to fetch private + organization repos, then compiles
    a daily summary for commits from the last 24 hours.

Fallback mode:
  - If PAT_GITHUB is missing, falls back to unauthenticated GitHub API for
    public repositories in GITHUB_ACCOUNTS (default: zero2webmaster).

Delivery routing is controlled by DELIVERY_METHOD:
  - email, airtable, slack, discord (comma-separated)
  - both == email,airtable (backward-compatible alias)
"""

from __future__ import annotations

import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    from github import Auth, Github, GithubException, RateLimitExceededException
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
HTML_FONT_SIZE = "18px"
DEFAULT_ACCOUNT = "zero2webmaster"
NO_WORK_MESSAGE = "No work today – hope you enjoyed the rest!"


def truncate(msg: str, length: int = MAX_MSG_LENGTH) -> str:
    first_line = msg.split("\n")[0].strip()
    if len(first_line) <= length:
        return first_line
    return first_line[: length - 3] + "..."


def _get_report_timezone() -> ZoneInfo:
    tz_name = (os.environ.get("EMAIL_TIMEZONE") or "America/New_York").strip()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        print(f"WARNING: Invalid EMAIL_TIMEZONE '{tz_name}', falling back to UTC")
        return ZoneInfo("UTC")


def _get_report_dates() -> tuple[str, str]:
    tz = _get_report_timezone()
    now_local = datetime.now(tz)
    date_ymd = now_local.strftime("%Y-%m-%d")
    date_subject = now_local.strftime("%a %b %d")
    return date_ymd, date_subject


def get_github_client() -> tuple[Github, bool, bool]:
    """Return (client, has_token, is_pat_token)."""
    token = os.environ.get("PAT_GITHUB")
    is_pat = bool(token)

    if not token:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            token = os.environ.get("PAT_GITHUB")
            is_pat = bool(token)
        except ImportError:
            pass

    # Optional fallbacks for local testing or GitHub Actions defaults.
    if not token:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        is_pat = False

    if token:
        return Github(auth=Auth.Token(token), per_page=100), True, is_pat

    print("WARNING: No PAT_GITHUB/GITHUB_TOKEN found. Using public unauthenticated mode.")
    print("  Public mode scans only public repos from GITHUB_ACCOUNTS.")
    return Github(per_page=100), False, False


def _list_public_account_repos(g: Github) -> list[Any]:
    raw = os.environ.get("GITHUB_ACCOUNTS", DEFAULT_ACCOUNT)
    accounts = [acct.strip() for acct in raw.split(",") if acct.strip()]
    if not accounts:
        accounts = [DEFAULT_ACCOUNT]

    dedup: dict[str, Any] = {}
    for account in accounts:
        try:
            org = g.get_organization(account)
            repos = list(org.get_repos(type="all"))
            print(f"  Loaded {len(repos)} repos from org '{account}'")
            for repo in repos:
                dedup[repo.full_name] = repo
            continue
        except GithubException as exc:
            if exc.status != 404:
                print(f"  Warning: could not read org '{account}' ({exc.status})")

        try:
            user = g.get_user(account)
            repos = list(user.get_repos(type="owner"))
            print(f"  Loaded {len(repos)} repos from user '{account}'")
            for repo in repos:
                dedup[repo.full_name] = repo
        except GithubException as exc:
            print(f"  Warning: could not read user '{account}' ({exc.status})")

    return sorted(dedup.values(), key=lambda r: r.full_name.lower())


def fetch_commits_with_retry(repo: Any, since: datetime, author: str | None, retries: int = MAX_RETRIES) -> list[Any]:
    for attempt in range(retries):
        try:
            if author:
                return list(repo.get_commits(since=since, author=author))
            return list(repo.get_commits(since=since))
        except RateLimitExceededException:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Rate limit exceeded after {retries} retries, skipping {repo.full_name}")
                return []
        except GithubException as exc:
            if exc.status == 409:
                return []
            if exc.status == 403 and attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  403 error on {repo.full_name}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Error fetching {repo.full_name}: {exc.status} {exc.data}")
                return []
    return []


AI_PROVIDERS = {
    "openrouter": ("OPENROUTER_API_KEY", "anthropic/claude-3-5-haiku"),
    "anthropic": ("ANTHROPIC_API_KEY", "claude-3-5-haiku-20241022"),
    "gemini": ("GOOGLE_API_KEY", "gemini-1.5-flash"),
    "openai": ("OPENAI_API_KEY", "gpt-4o-mini"),
}


def _get_ai_client_and_key() -> tuple[str | None, str | None, str | None]:
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
        print(f"  AI bullets: skipped (AI_PROVIDER='{provider}' must be one of: {valid})")
        return None, None, None

    key_env, model = AI_PROVIDERS[provider]
    api_key = os.environ.get(key_env) or (os.environ.get("GEMINI_API_KEY") if provider == "gemini" else None)
    if not api_key:
        return None, None, None
    return provider, api_key, model


def _normalize_bullet(line: str) -> str:
    bullet = line.strip().lstrip("-*• ").strip()
    if not bullet:
        return ""
    if bullet[-1] not in ".!?":
        bullet += "."
    return bullet


def generate_ai_repo_bullets(messages: list[str]) -> list[str] | None:
    """Return 3-5 bullets generated by AI, or None if unavailable."""
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        return None

    commit_list = "\n".join(f"- {truncate(m)}" for m in messages[:25])
    prompt = f"""Turn these git commit messages into exactly 3 to 5 concise summary bullets.

Requirements:
- Use a conversational, professional tone.
- Focus on features, refactors, bug fixes, and outcomes.
- Do not mention commit counts.
- Do not say "commit" or "commits".
- Return bullets only (one per line).

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
            raw = response.choices[0].message.content.strip()
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=220,
            )
            raw = response.choices[0].message.content.strip()
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=220,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=220),
            )
            raw = response.text.strip()
        else:
            return None
    except Exception as exc:
        print(f"  AI bullets error ({provider}): {exc}")
        return None

    bullets = [_normalize_bullet(line) for line in raw.splitlines()]
    bullets = [line for line in bullets if line]
    if not bullets:
        return None
    if len(bullets) < 3:
        while len(bullets) < 3:
            bullets.append("Kept momentum with steady maintenance and polish work.")
    return bullets[:5]


_PREFIX_RE = re.compile(r"^(feat|fix|refactor|chore|docs|test|ci|build|perf)(\([^)]+\))?!?:\s*", re.IGNORECASE)


def _clean_message(msg: str) -> str:
    first = truncate(msg)
    first = _PREFIX_RE.sub("", first)
    return first.strip(" -")


def _message_to_bullet(msg: str) -> str:
    raw = truncate(msg)
    cleaned = _clean_message(raw)
    lower = raw.lower()
    cleaned_lower = cleaned.lower()

    if lower.startswith("fix") or lower.startswith("bug"):
        text = f"Fixed {cleaned_lower}" if cleaned else raw
    elif lower.startswith("refactor"):
        text = f"Refactored {cleaned_lower}" if cleaned else raw
    elif lower.startswith("docs"):
        text = f"Updated docs for {cleaned_lower}" if cleaned else raw
    elif lower.startswith("test"):
        text = f"Expanded test coverage around {cleaned_lower}" if cleaned else raw
    elif lower.startswith("ci") or lower.startswith("build") or lower.startswith("workflow"):
        text = f"Improved CI/workflow around {cleaned_lower}" if cleaned else raw
    elif lower.startswith("add") or lower.startswith("feat") or lower.startswith("implement"):
        for prefix in ("add ", "added ", "implement ", "implemented ", "create ", "created "):
            if cleaned_lower.startswith(prefix):
                cleaned_lower = cleaned_lower[len(prefix):]
                break
        text = f"Added {cleaned_lower}" if cleaned else raw
    else:
        text = cleaned or raw

    text = text[0].upper() + text[1:] if text else "Delivered updates across this project"
    if text[-1] not in ".!?":
        text += "."
    return text


def _categorize_message(msg: str) -> str:
    lower = msg.lower()
    if any(k in lower for k in ("fix", "bug", "error", "hotfix")):
        return "bug fixes"
    if any(k in lower for k in ("refactor", "cleanup", "restructure")):
        return "refactors"
    if any(k in lower for k in ("feat", "feature", "add", "implement", "create", "launch")):
        return "feature delivery"
    if any(k in lower for k in ("docs", "readme", "changelog", "guide")):
        return "documentation"
    if any(k in lower for k in ("test", "pytest", "spec")):
        return "testing"
    if any(k in lower for k in ("workflow", "ci", "github actions", "deploy", "infra")):
        return "automation and ops"
    if any(k in lower for k in ("deps", "dependency", "bump", "upgrade")):
        return "dependency updates"
    return "general improvements"


def build_repo_bullets(messages: list[str]) -> list[str]:
    ai_bullets = generate_ai_repo_bullets(messages)
    if ai_bullets:
        return ai_bullets[:5]

    cats = Counter(_categorize_message(m) for m in messages)
    top_cats = [name for name, _ in cats.most_common(3)]
    if top_cats:
        if len(top_cats) == 1:
            first = f"Most of today's work centered on {top_cats[0]}."
        elif len(top_cats) == 2:
            first = f"Most of today's work centered on {top_cats[0]} and {top_cats[1]}."
        else:
            first = f"Most of today's work centered on {top_cats[0]}, {top_cats[1]}, and {top_cats[2]}."
    else:
        first = "Kept the project moving with focused updates and cleanup."

    bullets: list[str] = [first]
    seen: set[str] = set()
    for msg in messages[:10]:
        normalized = _clean_message(msg).lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        bullets.append(_message_to_bullet(msg))
        if len(bullets) >= 5:
            break

    while len(bullets) < 3:
        bullets.append("Kept momentum with steady maintenance and polish work.")
    return bullets[:5]


def _build_markdown_summary(
    date_subject: str,
    repos: list[dict[str, Any]],
    total_commits: int,
    total_repos: int,
) -> str:
    lines = [
        f"# Daily Cursor Work - {date_subject}",
        "",
    ]

    if not repos:
        lines += [
            NO_WORK_MESSAGE,
            "",
        ]
    else:
        commit_word = "commit" if total_commits == 1 else "commits"
        lines += [
            "Quick roundup from the last 24 hours across your GitHub projects:",
            "",
            f"**{total_commits} {commit_word}** across **{total_repos} active repos**",
            "",
        ]
        for repo in repos:
            lines.append(f"**{repo['repo_name']}**")
            for bullet in repo["bullets"]:
                lines.append(f"• {bullet}")
            lines.append("")

    lines += [
        "---",
        "",
        f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]
    return "\n".join(lines)


def generate_summary() -> dict[str, Any]:
    """Fetch commits, generate summary, and return structured data."""
    g, has_token, is_pat = get_github_client()
    date_ymd, date_subject = _get_report_dates()
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"Fetching commits since: {since.isoformat()}")

    author_login: str | None = None
    repos: list[Any]

    if has_token:
        try:
            auth_user = g.get_user()
            author_login = auth_user.login
            print(f"Authenticated as: {author_login}")
            repos = list(auth_user.get_repos(affiliation="owner,organization_member"))
            print(f"Found {len(repos)} accessible repositories (personal + org memberships)")
        except GithubException as exc:
            if is_pat and exc.status in (401, 403):
                print("ERROR: PAT_GITHUB is invalid or lacks required scopes.")
                print("  Required scopes: repo, read:user")
                print("  Update token: https://github.com/settings/tokens")
                sys.exit(1)
            print(f"WARNING: token auth unavailable ({exc.status}); using public fallback")
            repos = _list_public_account_repos(g)
    else:
        repos = _list_public_account_repos(g)

    repo_entries: list[dict[str, Any]] = []
    for repo in repos:
        if getattr(repo, "archived", False):
            continue
        commits = fetch_commits_with_retry(repo, since, author_login)
        if not commits:
            continue

        messages = [c.commit.message for c in commits]
        full_name = repo.full_name
        owner = full_name.split("/", 1)[0]
        bullets = build_repo_bullets(messages)
        repo_entries.append({
            "full_name": full_name,
            "repo_name": full_name.split("/", 1)[1],
            "url": repo.html_url,
            "owner": owner,
            "commits": len(messages),
            "messages": messages,
            "bullets": bullets,
            # Preserved field for Slack/Discord compatibility.
            "ai_summary": bullets[0] if bullets else None,
        })
        print(f"  {full_name}: {len(messages)} commit(s)")

    repo_entries.sort(key=lambda r: (-r["commits"], r["full_name"].lower()))
    total_commits = sum(repo["commits"] for repo in repo_entries)
    total_repos = len(repo_entries)

    markdown_body = _build_markdown_summary(
        date_subject=date_subject,
        repos=repo_entries,
        total_commits=total_commits,
        total_repos=total_repos,
    )
    html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
    html = f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'

    ai_summary_lines = []
    for repo in repo_entries:
        brief = " | ".join(repo["bullets"][:3])
        ai_summary_lines.append(f"- {repo['full_name']}: {brief}")

    return {
        "html": html,
        "markdown": markdown_body,
        "date": date_ymd,
        "subject_date": date_subject,
        "total_commits": total_commits,
        "total_repos": total_repos,
        "repos": repo_entries,
        "ai_summaries_text": "\n".join(ai_summary_lines),
        "has_commits": bool(repo_entries),
    }


VALID_DELIVERY_METHODS = {"email", "airtable", "slack", "discord"}


def parse_delivery_methods(raw: str | None) -> set[str]:
    raw = (raw or "email").lower().strip()
    if raw == "both":
        raw = "email,airtable"
    methods = {m.strip() for m in raw.split(",") if m.strip()}
    unknown = methods - VALID_DELIVERY_METHODS
    if unknown:
        valid_str = ", ".join(sorted(VALID_DELIVERY_METHODS))
        print(
            f"  WARNING: Unknown DELIVERY_METHOD value(s): {', '.join(sorted(unknown))} — ignoring. "
            f"Valid options: {valid_str}"
        )
        methods -= unknown
    if not methods:
        print("  WARNING: No valid delivery methods found, defaulting to 'email'")
        return {"email"}
    return methods


def send_to_slack(summary_data: dict) -> bool:
    from webhook_client import send_slack

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("  Slack: skipped (SLACK_WEBHOOK_URL not set)")
        return False

    print("  Slack: sending message...")
    return send_slack(webhook_url, summary_data)


def send_to_discord(summary_data: dict) -> bool:
    from webhook_client import send_discord

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("  Discord: skipped (DISCORD_WEBHOOK_URL not set)")
        return False

    print("  Discord: sending message...")
    return send_discord(webhook_url, summary_data)


def _get_airtable_config() -> dict[str, str] | None:
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
    from airtable_client import AirtableClient, AirtableError

    config = _get_airtable_config()
    if not config:
        return False

    client = AirtableClient(pat=config["pat"], base_id=config["base_id"])
    tbl_summaries = config["table_summaries"]
    tbl_repos = config["table_repos"]

    date_str = summary_data["date"]
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
        "AI Summaries": summary_data["ai_summaries_text"] or "(No repo bullets available)",
    }
    if repo_record_ids:
        fields["Repositories"] = repo_record_ids

    def _write_summary(with_repos: bool = True) -> bool:
        payload = fields.copy()
        if not with_repos and "Repositories" in payload:
            del payload["Repositories"]
        if existing_record:
            client.update_record(tbl_summaries, existing_record["id"], payload)
            return True
        record = client.create_record(tbl_summaries, payload)
        print(f"  Airtable: created daily summary record {record['id']} for {date_str}")
        return True

    if existing_record:
        try:
            _write_summary(with_repos=True)
            print(f"  Airtable: updated existing summary {existing_record['id']} for {date_str} (repos linked)")
            return True
        except AirtableError as exc:
            if getattr(exc, "status_code", None) == 422:
                try:
                    _write_summary(with_repos=False)
                    print("  Airtable: updated summary (Repositories field missing — run Setup Airtable)")
                    return True
                except AirtableError:
                    pass
            print(f"  Airtable: warning updating summary: {exc}")
            return True

    try:
        _write_summary(with_repos=True)
        return True
    except AirtableError as exc:
        if getattr(exc, "status_code", None) == 422:
            try:
                _write_summary(with_repos=False)
                print("  Airtable: created summary (Repositories link field missing — run Setup Airtable)")
                return True
            except AirtableError as retry_exc:
                print(f"  Airtable ERROR creating summary: {retry_exc}")
                return False
        print(f"  Airtable ERROR creating summary: {exc}")
        return False


def _find_or_create_repo(client: "AirtableClient", table_id: str, repo_info: dict) -> str | None:
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
        record = client.create_record(
            table_id,
            {
                "Name": full_name,
                "URL": repo_info["url"],
                "Owner": repo_info["owner"],
            },
        )
        print(f"  Airtable: created repo record for {full_name}")
        return record["id"]
    except AirtableError as exc:
        print(f"  Airtable ERROR creating repo '{full_name}': {exc}")
        return None


def main():
    print("=" * 50)
    print("Daily Cursor Work Summary Generator")
    print("=" * 50)

    summary_data = generate_summary()

    delivery_methods = parse_delivery_methods(os.environ.get("DELIVERY_METHOD"))
    print(f"\nDelivery methods: {', '.join(sorted(delivery_methods))}")

    archive_path = Path(f"{summary_data['date']}-GitHub-Daily-Summary.md")
    archive_path.write_text(summary_data["markdown"], encoding="utf-8")
    print(f"Archive written to: {archive_path}")

    email_path = Path(".tmp") / f"{summary_data['date']}-GitHub-Daily-Summary.html"
    email_path.parent.mkdir(exist_ok=True)
    email_path.write_text(summary_data["html"], encoding="utf-8")
    print(f"Email HTML written to: {email_path}")

    if "airtable" in delivery_methods and summary_data["has_commits"]:
        print("\n--- Airtable Delivery ---")
        write_to_airtable(summary_data)

    if "slack" in delivery_methods:
        print("\n--- Slack Delivery ---")
        send_to_slack(summary_data)

    if "discord" in delivery_methods:
        print("\n--- Discord Delivery ---")
        send_to_discord(summary_data)

    send_email = "email" in delivery_methods
    if not send_email:
        active = ", ".join(sorted(delivery_methods - {"email"}))
        print(f"\nEmail step: skipped (delivery is {active} only)")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write("has_summary=true\n")
            fh.write(f"archive_file={archive_path}\n")
            fh.write(f"email_file={email_path}\n")
            fh.write(f"subject_date={summary_data['subject_date']}\n")
            fh.write(f"send_email={'true' if send_email else 'false'}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
