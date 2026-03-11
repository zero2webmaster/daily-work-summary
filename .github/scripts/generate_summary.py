#!/usr/bin/env python3
"""
Daily Work Summary Generator

Fetches all commits from the last 24 hours across every repository
the authenticated GitHub user owns, then generates a smart grouped
summary as Markdown.

Runs as part of the GitHub Actions workflow, but can also be tested
locally with PAT_GITHUB set in environment or .env file.
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from github import Github, GithubException, RateLimitExceededException
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)

MAX_MSG_LENGTH = 80
MAX_COMMITS_SHOWN = 5
MAX_RETRIES = 3
SUMMARY_DIR = "summaries"


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

    return Github(token, per_page=100)


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


def format_commit_summary(messages: list[str]) -> str:
    """Create an intelligent one-line summary of commit messages."""
    cleaned = []
    for msg in messages:
        first_line = truncate(msg)
        prefix_stripped = first_line
        for prefix in ("feat:", "fix:", "chore:", "docs:", "refactor:", "style:", "test:", "ci:", "build:", "perf:"):
            if prefix_stripped.lower().startswith(prefix):
                prefix_stripped = prefix_stripped[len(prefix):].strip()
                break
        cleaned.append(prefix_stripped)

    count = len(cleaned)
    shown = cleaned[:MAX_COMMITS_SHOWN]
    summary_parts = "; ".join(shown)
    extra = count - len(shown)

    if extra > 0:
        return f"{count} changes: {summary_parts} (+{extra} more)"
    return f"{count} change{'s' if count != 1 else ''}: {summary_parts}"


def generate_summary() -> str:
    g = get_github_client()
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"Fetching commits since: {since.isoformat()}")

    repo_commits: dict[str, list[str]] = {}

    repos = list(user.get_repos(affiliation="owner,organization_member"))
    print(f"Found {len(repos)} repositories")

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login)
        if commits:
            messages = [c.commit.message for c in commits]
            repo_commits[repo.full_name] = messages
            print(f"  {repo.full_name}: {len(commits)} commits")

    if not repo_commits:
        return "No commits today — well rested! ✅\n"

    sorted_repos = sorted(repo_commits.items(), key=lambda x: len(x[1]), reverse=True)

    total_commits = sum(len(msgs) for msgs in repo_commits.values())
    lines = [
        f"# Daily Work Summary — {datetime.now(timezone.utc).strftime('%a %b %d, %Y')}",
        "",
        f"**{total_commits} commits** across **{len(repo_commits)} repos**",
        "",
        "---",
        "",
    ]

    for repo_name, messages in sorted_repos:
        count = len(messages)
        summary = format_commit_summary(messages)

        lines.append(f"## {repo_name}")
        lines.append(f"**{count} commit{'s' if count != 1 else ''}**")
        lines.append(f"- {summary}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 50)
    print("Daily Work Summary Generator")
    print("=" * 50)

    try:
        summary = generate_summary()
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

    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary_path = Path(SUMMARY_DIR) / f"daily-summary-{today}.md"

    summary_path.write_text(summary)
    print(f"\nSummary written to: {summary_path}")
    print(f"\n{'=' * 50}")
    print(summary)


if __name__ == "__main__":
    main()
