#!/usr/bin/env python3
"""
Daily GitHub Work Summary generator.

Collects commits from the last 24 hours across personal + org-member repos,
builds a conversational per-project summary (3-5 bullets each), writes:
  - YYYY-MM-DD-GitHub-Daily-Summary.md (repo archive)
  - .tmp/daily-summary-email-YYYY-MM-DD.html (email body)
and optionally sends to Airtable/Slack/Discord.
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

MAX_MSG_LENGTH = 80
MAX_RETRIES = 3
TMP_DIR = ".tmp"
ARCHIVE_FILENAME_TEMPLATE = "{date}-GitHub-Daily-Summary.md"
EMAIL_FILENAME_TEMPLATE = "daily-summary-email-{date}.html"
NO_WORK_MESSAGE = "No work today – hope you enjoyed the rest!"
HTML_FONT_SIZE = "18px"


def get_github_client() -> Github:
    token = os.environ.get("PAT_GITHUB")
    if not token:
        try:
            from dotenv import load_dotenv

            load_dotenv()
            token = os.environ.get("PAT_GITHUB")
        except ImportError:
            pass

    # Automation/local fallback when PAT_GITHUB is not injected.
    if not token:
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            token = result.stdout.strip() or None
            if token:
                print("Using token from authenticated gh CLI session.")
        except Exception:
            token = None

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
            return list(repo.get_commits(since=since, author=author))
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


COMMIT_PREFIX_RE = re.compile(
    r"^(feat|fix|refactor|chore|docs|test|ci|build|perf|style)(\([^)]+\))?!?:\s*",
    re.IGNORECASE,
)


def _clean_message(msg: str, length: int = 100) -> str:
    cleaned = COMMIT_PREFIX_RE.sub("", truncate(msg, length)).strip(" .-")
    return cleaned or truncate(msg, length)


def _categorize(msg: str) -> str:
    lower = msg.lower()
    if any(k in lower for k in ("feat", "feature", "add ", "implement", "introduc", "new ")):
        return "feature"
    if any(k in lower for k in ("fix", "bug", "resolve", "hotfix", "patch")):
        return "fix"
    if any(k in lower for k in ("refactor", "cleanup", "restructure", "rename", "simplif")):
        return "refactor"
    if any(k in lower for k in ("test", "pytest", "unit test", "integration test", "assert")):
        return "test"
    if any(k in lower for k in ("doc", "readme", "comment", "guide")):
        return "docs"
    if any(k in lower for k in ("ci", "workflow", "deploy", "release", "build", "infra")):
        return "ops"
    if any(k in lower for k in ("chore", "bump", "deps", "dependenc", "lint", "format")):
        return "chore"
    return "accomplishment"


def _join_highlights(items: list[str]) -> str:
    unique: list[str] = []
    seen: set[str] = set()
    for raw in items:
        cleaned = _clean_message(raw)
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            unique.append(cleaned)
        if len(unique) >= 2:
            break
    if not unique:
        return "ongoing project updates"
    if len(unique) == 1:
        return unique[0]
    return f"{unique[0]}; {unique[1]}"


def generate_repo_bullets(messages: list[str], ai_summary: str | None) -> list[str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for msg in messages:
        grouped[_categorize(msg)].append(msg)

    templates = {
        "feature": "Shipped feature work around {highlights}.",
        "fix": "Fixed issues around {highlights}.",
        "refactor": "Refactored codepaths tied to {highlights}.",
        "test": "Improved test coverage and validation for {highlights}.",
        "docs": "Updated docs and guidance for {highlights}.",
        "ops": "Handled CI/deployment plumbing for {highlights}.",
        "chore": "Knocked out maintenance tasks touching {highlights}.",
        "accomplishment": "Made additional progress on {highlights}.",
    }
    priority = {
        "feature": 0,
        "fix": 1,
        "refactor": 2,
        "test": 3,
        "docs": 4,
        "ops": 5,
        "chore": 6,
        "accomplishment": 7,
    }

    bullets: list[str] = []
    if ai_summary:
        bullets.append(ai_summary.rstrip(".") + ".")

    ordered = sorted(grouped.items(), key=lambda kv: (-len(kv[1]), priority.get(kv[0], 99)))
    for bucket, bucket_msgs in ordered:
        bullets.append(templates[bucket].format(highlights=_join_highlights(bucket_msgs)))
        if len(bullets) >= 5:
            break

    i = 0
    while len(bullets) < 3 and i < len(messages):
        bullets.append(f"Also iterated on {_clean_message(messages[i])}.")
        i += 1

    while len(bullets) < 3:
        bullets.append("Kept momentum going with follow-up polish and cleanup.")

    return bullets[:5]


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
        print(f"  AI summary skipped: invalid AI_PROVIDER '{provider}'")
        return None, None, None

    key_env, model = AI_PROVIDERS[provider]
    api_key = os.environ.get(key_env) or (os.environ.get("GEMINI_API_KEY") if provider == "gemini" else None)
    if not api_key:
        return None, None, None

    return provider, api_key, model


def generate_ai_repo_summary(messages: list[str]) -> str | None:
    provider, api_key, model = _get_ai_client_and_key()
    if not provider or not api_key:
        return None

    commit_list = "\n".join(truncate(m) for m in messages[:20])
    prompt = f"""Write one concise, conversational sentence summarizing these commits.
Focus on features, fixes, refactors, and accomplishments.
Do not mention commit counts or list commits.

Commits:
{commit_list}"""

    try:
        if provider in ("openrouter", "openai"):
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1" if provider == "openrouter" else None,
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            return (resp.choices[0].message.content or "").strip().rstrip(".")

        if provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=model,
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip().rstrip(".")

        if provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            resp = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=80),
            )
            return resp.text.strip().rstrip(".")
    except Exception as exc:
        print(f"  AI summary error: {exc}")
        return None

    return None


def _build_markdown(today: str, repos: list[dict[str, Any]], total_commits: int) -> str:
    if not repos:
        return NO_WORK_MESSAGE

    lines: list[str] = [
        f"# Daily Cursor Work - {today}",
        "",
        f"Sorted by activity: **{total_commits} commits** across **{len(repos)} repos**.",
        "",
    ]

    for repo in repos:
        lines.append(f"**{repo['full_name']}**")
        for bullet in repo["summary_bullets"]:
            lines.append(f"• {bullet}")
        lines.append("")

    lines.append(f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")
    return "\n".join(lines).strip() + "\n"


def _markdown_to_email_html(markdown_body: str) -> str:
    md_for_html = markdown_body.replace("\n• ", "\n* ")
    html_content = markdown_lib.markdown(md_for_html, extensions=["nl2br"])
    return f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'


def generate_summary() -> dict[str, Any]:
    g = get_github_client()
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Fetching commits since: {since.isoformat()}")

    all_repos = list(user.get_repos(affiliation="owner,organization_member"))
    print(f"Found {len(all_repos)} repositories")

    active_repos: list[dict[str, Any]] = []
    for repo in all_repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login)
        if not commits:
            continue

        messages = [c.commit.message for c in commits]
        owner, repo_name = repo.full_name.split("/", 1)
        ai_summary = generate_ai_repo_summary(messages)
        summary_bullets = generate_repo_bullets(messages, ai_summary)

        active_repos.append(
            {
                "full_name": repo.full_name,
                "url": repo.html_url,
                "owner": owner,
                "repo_name": repo_name,
                "commits": len(commits),
                "messages": messages,
                "ai_summary": ai_summary,
                "summary_bullets": summary_bullets,
            }
        )
        print(f"  {repo.full_name}: {len(commits)} commits")

    active_repos.sort(key=lambda r: (-r["commits"], r["full_name"].lower()))
    total_commits = sum(r["commits"] for r in active_repos)

    markdown_body = _build_markdown(today, active_repos, total_commits)
    html_body = _markdown_to_email_html(markdown_body)
    ai_summaries_text = "\n".join(
        f"- {r['full_name']}: {r['ai_summary']}" for r in active_repos if r.get("ai_summary")
    )

    return {
        "html": html_body,
        "markdown": markdown_body,
        "date": today,
        "total_commits": total_commits,
        "total_repos": len(active_repos),
        "repos": active_repos,
        "ai_summaries_text": ai_summaries_text,
        "has_commits": bool(active_repos),
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

    return methods or {"email"}


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
    for repo_info in repos:
        repo_record_id = _find_or_create_repo(client, tbl_repos, repo_info)
        if repo_record_id:
            repo_record_ids.append(repo_record_id)

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
        payload = fields.copy()
        if not with_repos and "Repositories" in payload:
            del payload["Repositories"]
        if existing_record:
            client.update_record(tbl_summaries, existing_record["id"], payload)
            return True
        client.create_record(tbl_summaries, payload)
        return True

    try:
        _write_summary(with_repos=True)
        return True
    except AirtableError as exc:
        if getattr(exc, "status_code", None) == 422:
            try:
                _write_summary(with_repos=False)
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
        return record["id"]
    except AirtableError as exc:
        print(f"  Airtable ERROR creating repo '{full_name}': {exc}")
        return None


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
        if e.status == 403:
            print("ERROR: PAT_GITHUB has insufficient permissions.")
            print("  Required scopes: repo, read:user")
            print("  Update at: https://github.com/settings/tokens")
            sys.exit(1)
        raise

    delivery_methods = parse_delivery_methods(os.environ.get("DELIVERY_METHOD"))
    print(f"\nDelivery methods: {', '.join(sorted(delivery_methods))}")

    archive_path = Path(ARCHIVE_FILENAME_TEMPLATE.format(date=summary_data["date"]))
    archive_path.write_text(summary_data["markdown"], encoding="utf-8")
    print(f"Archive written to: {archive_path}")

    Path(TMP_DIR).mkdir(exist_ok=True)
    email_path = Path(TMP_DIR) / EMAIL_FILENAME_TEMPLATE.format(date=summary_data["date"])
    email_path.write_text(summary_data["html"], encoding="utf-8")
    print(f"Email HTML written to: {email_path}")

    if "airtable" in delivery_methods:
        print("\n--- Airtable Delivery ---")
        write_to_airtable(summary_data)

    if "slack" in delivery_methods:
        print("\n--- Slack Delivery ---")
        send_to_slack(summary_data)

    if "discord" in delivery_methods:
        print("\n--- Discord Delivery ---")
        send_to_discord(summary_data)

    send_email = "email" in delivery_methods
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"send_email={'true' if send_email else 'false'}\n")
            fh.write(f"archive_file={archive_path}\n")
            fh.write(f"email_file={email_path}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["markdown"])


if __name__ == "__main__":
    main()
