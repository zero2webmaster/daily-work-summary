#!/usr/bin/env python3
"""
Webhook Delivery Client — Slack and Discord

Formats daily work summary data into Slack Block Kit messages and Discord
embeds, then POSTs them to the respective webhook URLs.

Both functions handle message length limits:
  - Slack: 3 000 chars per text block, up to 50 blocks
  - Discord: 4 096 chars per embed description, 6 000 chars total per message
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests

# ------------------------------------------------------------------ #
#  Constants
# ------------------------------------------------------------------ #

SLACK_MAX_BLOCK_TEXT = 3000   # Slack API limit per section text element
DISCORD_MAX_DESC = 4000       # Conservative limit for embed description
DISCORD_MAX_FIELD_VALUE = 1000  # Conservative limit for embed field values
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2          # seconds

Z2W_URL = "https://zero2webmaster.com/kerry-kriger"
REPO_URL = "https://github.com/zero2webmaster/daily-work-summary"
NO_WORK_MESSAGE = "No work today – hope you enjoyed the rest!"


# ------------------------------------------------------------------ #
#  Shared helpers
# ------------------------------------------------------------------ #

def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _post_with_retry(url: str, payload: dict, label: str) -> bool:
    """POST JSON to a webhook URL with exponential-backoff retry.

    Returns True on success, False on failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=15,
            )
            if resp.status_code in (200, 204):
                print(f"  {label}: message sent successfully (HTTP {resp.status_code})")
                return True

            # 429 = rate limit — honour Retry-After header if present
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", RETRY_BASE_DELAY * (attempt + 1)))
                print(f"  {label}: rate limited, waiting {retry_after:.0f}s...")
                time.sleep(retry_after)
                continue

            print(f"  {label}: HTTP {resp.status_code} — {resp.text[:200]}")
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY ** (attempt + 1)
                print(f"  {label}: retrying in {delay}s...")
                time.sleep(delay)
            else:
                return False

        except requests.RequestException as exc:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY ** (attempt + 1)
                print(f"  {label}: network error ({exc}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"  {label}: failed after {MAX_RETRIES} attempts: {exc}")
                return False

    return False


# ------------------------------------------------------------------ #
#  Slack
# ------------------------------------------------------------------ #

def _build_slack_repo_text(repos: list[dict[str, Any]]) -> str:
    """Build the per-repo section of the Slack message."""
    lines: list[str] = []
    for repo in repos:
        count = repo["commits"]
        label = f"{count} commit{'s' if count != 1 else ''}"
        repo_name = repo["full_name"].split("/", 1)[-1]
        url = repo.get("url", "")
        lines.append(f"*<{url}|{repo_name}>* ({label})")
        highlights = repo.get("summary_bullets") or []
        if highlights:
            for point in highlights[:5]:
                lines.append(f"• {point}")
        else:
            for msg in repo["messages"]:
                first_line = msg.split("\n")[0].strip()
                if len(first_line) > 80:
                    first_line = first_line[:77] + "..."
                lines.append(f"• {first_line}")
        lines.append("")
    return "\n".join(lines).strip()


def send_slack(webhook_url: str, summary_data: dict[str, Any]) -> bool:
    """Send a formatted Slack message via incoming webhook.

    Returns True on success, False on failure.
    """
    date = summary_data.get("date", "")
    total_commits = summary_data.get("total_commits", 0)
    total_repos = summary_data.get("total_repos", 0)
    repos = summary_data.get("repos", [])
    has_commits = summary_data.get("has_commits", False)

    # Header block (always present)
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📋 Daily Work Summary — {date}"},
        }
    ]

    if not has_commits:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": NO_WORK_MESSAGE},
        })
    else:
        # Stats bar
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{total_commits} commit{'s' if total_commits != 1 else ''}* across *{total_repos} repo{'s' if total_repos != 1 else ''}*",
            },
        })
        blocks.append({"type": "divider"})

        # Per-repo sections — respect Slack's 50-block limit
        for repo in repos:
            count = repo["commits"]
            label = f"{count} commit{'s' if count != 1 else ''}"
            repo_name = repo["full_name"].split("/", 1)[-1]
            url = repo.get("url", "")

            header_text = f"*<{url}|{repo_name}>* ({label})"
            highlights = repo.get("summary_bullets") or []
            commit_lines = []
            if highlights:
                commit_lines.extend([f"• {point}" for point in highlights[:5]])
            else:
                for msg in repo["messages"]:
                    first_line = msg.split("\n")[0].strip()
                    if len(first_line) > 80:
                        first_line = first_line[:77] + "..."
                    commit_lines.append(f"• {first_line}")

            body = "\n".join(commit_lines)
            full_text = f"{header_text}\n{body}"
            full_text = _truncate(full_text, SLACK_MAX_BLOCK_TEXT)

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": full_text},
            })

            # Hard cap: Slack allows 50 blocks per message
            if len(blocks) >= 47:
                remaining = len(repos) - repos.index(repo) - 1
                if remaining > 0:
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"_...and {remaining} more repo(s)_"},
                    })
                break

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"<{Z2W_URL}|Daily Work Summary> • <{REPO_URL}|View on GitHub>",
            }
        ],
    })

    payload = {
        "blocks": blocks,
        # Fallback plain text for notifications
        "text": f"Daily Work Summary — {date}: {total_commits} commit(s) across {total_repos} repo(s)",
    }

    return _post_with_retry(webhook_url, payload, "Slack")


# ------------------------------------------------------------------ #
#  Discord
# ------------------------------------------------------------------ #

def _build_discord_description(repos: list[dict[str, Any]]) -> str:
    """Build the embed description (repo list) for Discord."""
    lines: list[str] = []
    for repo in repos:
        count = repo["commits"]
        label = f"{count} commit{'s' if count != 1 else ''}"
        url = repo.get("url", "")
        full_name = repo["full_name"]
        lines.append(f"**[{full_name}]({url})** ({label})")
        highlights = repo.get("summary_bullets") or []
        if highlights:
            for point in highlights[:5]:
                lines.append(f"• {point}")
        else:
            for msg in repo["messages"]:
                first_line = msg.split("\n")[0].strip()
                if len(first_line) > 80:
                    first_line = first_line[:77] + "..."
                lines.append(f"• {first_line}")
        lines.append("")

    return _truncate("\n".join(lines).strip(), DISCORD_MAX_DESC)


def send_discord(webhook_url: str, summary_data: dict[str, Any]) -> bool:
    """Send a formatted Discord embed via incoming webhook.

    Returns True on success, False on failure.
    """
    date = summary_data.get("date", "")
    total_commits = summary_data.get("total_commits", 0)
    total_repos = summary_data.get("total_repos", 0)
    repos = summary_data.get("repos", [])
    has_commits = summary_data.get("has_commits", False)

    # Discord embed colour: green when work done, grey when no commits
    color = 0x2ECC71 if has_commits else 0x95A5A6  # emerald green / concrete grey

    if not has_commits:
        description = NO_WORK_MESSAGE
    else:
        description = _build_discord_description(repos)

    embed: dict[str, Any] = {
        "title": f"📋 Daily Work Summary — {date}",
        "description": description,
        "color": color,
        "footer": {
            "text": f"Zero2Webmaster Daily Summary  •  {REPO_URL}",
        },
    }

    if has_commits:
        embed["fields"] = [
            {
                "name": "Total Commits",
                "value": str(total_commits),
                "inline": True,
            },
            {
                "name": "Repos Active",
                "value": str(total_repos),
                "inline": True,
            },
        ]

    payload: dict[str, Any] = {"embeds": [embed]}

    return _post_with_retry(webhook_url, payload, "Discord")
