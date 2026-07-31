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
import sys
import time
from collections import defaultdict
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

# Machine-readable provenance stamped into the top of every archived summary as
# an inert HTML comment (invisible in email clients and in the command center's
# render). It states the day the file REPORTS ON, which the filename alone can no
# longer be trusted to convey: every summary written between 2026-06-18 and
# 2026-07-31 was named for the day the cron ran rather than the day it covers.
#
# The per-day idempotency guard requires this stamp to match before it treats an
# existing file as already-sent, so a legacy misdated file is regenerated in
# place instead of silently suppressing that day's email.
SUMMARY_SCHEMA = "daily-summary/v2"


def summary_stamp(covers: str) -> str:
    return f'<!-- {SUMMARY_SCHEMA} covers="{covers}" -->'


# Repos whose commits are agent/coordination BOOKKEEPING rather than product work.
# They are real commits and stay in the totals, but they're rendered as a single
# collapsed line with no bullets and no AI call.
#
# Why: every Z2W agent writes its session notes into the coordination repo, so it
# routinely tops a digest that sorts purely by commit count — on 2026-06-22 it
# contributed 64 commits and out-ranked every product repo, spending roughly a
# third of the email on bulletin bookkeeping. Kerry's call (2026-07-31): keep the
# signal that agents were active, drop the line-by-line detail.
#
# Override with the COLLAPSE_REPOS Action variable (comma-separated repo names);
# set it to an empty-ish value like "none" to disable collapsing entirely.
DEFAULT_COLLAPSED_REPOS = {"z2w-agent-coordination"}


def get_collapsed_repos() -> set[str]:
    raw = os.environ.get("COLLAPSE_REPOS")
    if raw is None or not raw.strip():
        return set(DEFAULT_COLLAPSED_REPOS)
    if raw.strip().lower() in {"none", "off", "false"}:
        return set()
    return {r.strip() for r in raw.split(",") if r.strip()}

DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_SEND_HOUR = 22
DEFAULT_SEND_MINUTE = 30
# Wide by design. GitHub throttles the "hourly" cron for low-traffic repos and
# routinely fires nothing between ~00:30 and ~04:30 ET — so a narrow window that
# straddles that gap never catches a run and no summary is ever sent. 480 minutes
# (8h) lets the first run after the target time still send, while the per-day
# idempotency guard in main() prevents a wide window from double-sending.
DEFAULT_SEND_WINDOW_MIN = 480

SCHEDULE_DOCS_URL = (
    "https://github.com/zero2webmaster/daily-work-summary"
    "#customizing-the-email-schedule"
)

# Skill Vault tally (headline stat in the email). The Vault's per-day created/
# improved counts + running total are pre-computed into a versioned JSON artifact
# in the coordination repo (schema skill-vault-stats/v1; see that repo's
# stats/README.md). We read that artifact rather than the private z2w-skill-vault
# repo directly, so no extra token scope is needed beyond PAT_GITHUB's org read.
COORDINATION_REPO = "zero2webmaster/z2w-agent-coordination"
SKILL_VAULT_STATS_PATH = "stats/skill-vault.json"


def _get_email_timezone() -> ZoneInfo:
    """Return the configured EMAIL_TIMEZONE as a ZoneInfo, falling back to UTC.

    Admins set EMAIL_TIMEZONE in GitHub Actions → Variables to an IANA zone
    name (e.g. America/New_York, Europe/London, Asia/Singapore). If unset or
    invalid, falls back gracefully so the run still completes.
    """
    tz_name = os.environ.get("EMAIL_TIMEZONE", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        print(f"WARNING: EMAIL_TIMEZONE='{tz_name}' is not a valid IANA zone; falling back to UTC")
        return ZoneInfo("UTC")


def _now_local() -> datetime:
    return datetime.now(_get_email_timezone())


def _parse_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"WARNING: {name}='{raw}' is not an integer; falling back to {default}")
        return default


def _target_local(now_local: datetime | None = None) -> datetime:
    """Return the most recent PAST occurrence of the configured send time.

    This is the single anchor for BOTH the send-window guard and the summary's
    date label, and the two must never disagree.

    GitHub's scheduler is throttled hard enough that the nightly job almost
    always lands AFTER midnight — a 23:00 America/New_York send slot is
    typically delivered around 00:30 the next morning. That run is delivering
    the digest for the *previous* evening's slot, so both the window it fetches
    and the date it prints must be the previous day. Labeling it with the
    wall-clock date at run time is what produced the long-standing off-by-one
    ("Daily Work Summary — Fri Jul 31" containing Thursday's commits).

    Falls back to the module defaults on an invalid HH:MM so labeling always
    yields a usable date; should_run_now() does the strict validation.
    """
    tz = _get_email_timezone()
    hour = _parse_int_env("EMAIL_SEND_HOUR", DEFAULT_SEND_HOUR)
    minute = _parse_int_env("EMAIL_SEND_MINUTE", DEFAULT_SEND_MINUTE)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        hour, minute = DEFAULT_SEND_HOUR, DEFAULT_SEND_MINUTE

    if now_local is None:
        now_local = datetime.now(tz)

    target = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # Step back a day when we're before today's send time, so the target is
    # always the slot we are currently delivering rather than a future one.
    if now_local < target:
        target -= timedelta(days=1)
    return target


def should_run_now() -> tuple[bool, str]:
    """Decide whether the current wall-clock time falls inside the configured
    send window. Returns (allowed, reason_string).

    Admins set:
      EMAIL_TIMEZONE          (IANA zone, e.g. America/New_York)
      EMAIL_SEND_HOUR         (0-23, local hour, default 22)
      EMAIL_SEND_MINUTE       (0-59, local minute, default 30)
      EMAIL_SEND_WINDOW_MIN   (minutes after target that still count, default 60)

    The workflow fires hourly; this guard ensures only the run nearest the
    target local time actually sends the email. The window is one-sided
    (only AFTER the target) so a delayed cron still fires; it never fires
    early. GitHub's scheduler is heavily throttled, so the window is wide by
    default (see DEFAULT_SEND_WINDOW_MIN) and main() dedupes per local day.
    """
    tz = _get_email_timezone()
    hour = _parse_int_env("EMAIL_SEND_HOUR", DEFAULT_SEND_HOUR)
    minute = _parse_int_env("EMAIL_SEND_MINUTE", DEFAULT_SEND_MINUTE)
    window = _parse_int_env("EMAIL_SEND_WINDOW_MIN", DEFAULT_SEND_WINDOW_MIN)

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return False, f"invalid target time {hour:02d}:{minute:02d} (must be 00:00–23:59)"

    now_local = datetime.now(tz)
    # Anchor to the most recent PAST occurrence of HH:MM (see _target_local).
    # Without this, a cron run that lands after midnight (the only runs GitHub
    # reliably fires are ~00:39–02:01 ET) computes a target ~22h in the future,
    # making delta hugely negative so the guard never fires.
    target = _target_local(now_local)
    delta_min = (now_local - target).total_seconds() / 60

    label = (
        f"target {hour:02d}:{minute:02d} {tz.key} ({target.strftime('%b %d')}), "
        f"now {now_local.strftime('%H:%M %Z')}, "
        f"delta {delta_min:+.0f}m, window 0..{window}m"
    )
    if 0 <= delta_min <= window:
        return True, f"within window ({label})"
    return False, f"outside window ({label})"


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


def fetch_commits_with_retry(repo, since, author, retries=MAX_RETRIES, until=None):
    for attempt in range(retries):
        try:
            # until is set only for backfill (a closed [since, until] window);
            # the normal nightly run passes until=None ("since 24h ago, to HEAD").
            kwargs = {"since": since, "author": author}
            if until is not None:
                kwargs["until"] = until
            commits = list(repo.get_commits(**kwargs))
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
    "openrouter": ("OPENROUTER_API_KEY", "anthropic/claude-haiku-4.5"),
    "anthropic": ("ANTHROPIC_API_KEY", "claude-haiku-4-5-20251001"),
    "gemini": ("GOOGLE_API_KEY", "gemini-2.5-flash"),  # GOOGLE_API_KEY or GEMINI_API_KEY
    "openai": ("OPENAI_API_KEY", "gpt-5-mini"),
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
- Write in plain English suitable for a non-developer reader.
- Avoid jargon, version numbers, project codenames (e.g. "Phase 6.5", "Option D", "Slice X"), and framework references.
- When the commits describe user-visible changes, lead with what the user can now do. Otherwise describe the area of work in passive, neutral terms — do NOT invent generic users or teams that aren't named in the commits (e.g., never say "The team improved..." or "The development team enhanced...").
- Keep it to one short sentence. Do not pad with a second clause joined by "and" unless the commits genuinely span two distinct areas.
- Do NOT list or enumerate commits (e.g., never say "2 changes: X; Y" or "3 commits: A, B, C")
- Do NOT say how many commits there were
- Describe the type of work and what area it touched (e.g., "Authentication and dashboard UI were tightened, and the nightly sync now emails on failure.")
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


def _resolve_window() -> tuple[datetime, datetime | None, str]:
    """Return (since_utc, until_utc_or_None, date_label) for this run.

    Normal nightly run: the calendar day of the send slot being delivered —
    [D 00:00 local, D 23:59:59 local], clamped to now so a pre-midnight run
    can't claim commits that haven't happened yet. D comes from _target_local(),
    NOT from the wall-clock date at run time: GitHub's throttled scheduler
    usually fires the 23:00 slot around 00:30 the following morning, and that
    run is reporting the previous day's work, so it must be labeled with the
    previous day. (Before this, the nightly path used a rolling 24h window
    labeled `now`, which is why a 00:31 run on Jul 31 fetched Jul 30's commits
    and then printed "Fri Jul 31" over them.)

    Backfill (env BACKFILL_DATE=YYYY-MM-DD): a CLOSED window covering that whole
    calendar day in EMAIL_TIMEZONE — [D 00:00 local, D 23:59:59 local] — labeled D.

    Both paths now use identical calendar-day semantics, so a nightly summary
    and a backfilled one for the same date cover exactly the same commits.
    Calendar-day boundaries give clean, gap-free, non-overlapping coverage, and
    "the summary for June 10 = what you committed on June 10" is the most
    intuitive reading of the archive.
    """
    tz = _get_email_timezone()
    backfill = (os.environ.get("BACKFILL_DATE") or "").strip()

    if backfill:
        try:
            d = datetime.strptime(backfill, "%Y-%m-%d").date()
        except ValueError:
            print(f"ERROR: BACKFILL_DATE='{backfill}' is not YYYY-MM-DD.")
            sys.exit(1)
        clamp_to_now = False
        print(f"BACKFILL mode: whole local day {backfill} ({tz.key})")
    else:
        d = _target_local().date()
        clamp_to_now = True

    start_local = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=tz)
    # A run that fires BEFORE its own send slot's midnight (rare — GitHub almost
    # always delivers after midnight) must not claim the rest of the evening.
    if clamp_to_now:
        now_local = datetime.now(tz)
        if end_local > now_local:
            end_local = now_local

    since = start_local.astimezone(timezone.utc)
    until = end_local.astimezone(timezone.utc)
    return since, until, d.isoformat()


def format_skill_vault_tally(stats: dict, today: str) -> str | None:
    """Build the one-line Skill Vault headline from a skill-vault-stats/v1 dict.

    Returns a Markdown line (e.g. "🧠 **Skill Vault:** 3 created, 5 improved
    today · 28 skills total") or None if the artifact has no usable numbers.
    Pure/offline so it can be unit-tested without GitHub.
    """
    if not isinstance(stats, dict):
        return None

    totals = stats.get("totals") or {}
    total_skills = totals.get("skills")
    by_day = stats.get("by_day") or {}
    as_of = stats.get("as_of")

    parts: list[str] = []

    today_entry = by_day.get(today) if isinstance(by_day, dict) else None
    if isinstance(today_entry, dict):
        created = today_entry.get("created", 0) or 0
        improved = today_entry.get("improved", 0) or 0
        seg = []
        if created:
            seg.append(f"{created} created")
        if improved:
            seg.append(f"{improved} improved")
        if seg:
            parts.append(", ".join(seg) + " today")

    if total_skills is not None:
        parts.append(f"{total_skills} skills total")

    if not parts:
        return None

    line = "🧠 **Skill Vault:** " + " · ".join(parts)
    # Surface staleness: the artifact only refreshes when a Vault session ends,
    # so if its latest day predates today we don't actually know today's counts.
    # Note the as-of date rather than implying "0 created today".
    if as_of and as_of != today and not isinstance(today_entry, dict):
        line += f" *(Vault stats as of {as_of})*"
    return line


def fetch_skill_vault_tally(g: Github, today: str) -> str | None:
    """Read the pre-computed Skill Vault stats artifact from the coordination
    repo and return a one-line Markdown headline for the email.

    NEVER raises. This is an optional adornment on Kerry's morning email; any
    failure (repo not accessible, file missing, malformed JSON) silently skips
    the tally rather than breaking the digest. Disable with SKILL_VAULT_TALLY=0.
    """
    if (os.environ.get("SKILL_VAULT_TALLY", "true").strip().lower()
            in {"0", "false", "no", "off"}):
        print("  Skill Vault tally: disabled via SKILL_VAULT_TALLY")
        return None
    try:
        import json
        repo = g.get_repo(COORDINATION_REPO)
        content = repo.get_contents(SKILL_VAULT_STATS_PATH)
        stats = json.loads(content.decoded_content.decode("utf-8"))
        line = format_skill_vault_tally(stats, today)
        if line:
            print(f"  Skill Vault tally: {line}")
        else:
            print("  Skill Vault tally: skipped (artifact had no usable totals)")
        return line
    except Exception as e:
        print(f"  Skill Vault tally: skipped ({type(e).__name__}: {e})")
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

    since, until, today = _resolve_window()
    print(f"Fetching commits since: {since.isoformat()}")
    if until is not None:
        print(f"Fetching commits until: {until.isoformat()}")
    print(f"Local date label: {today} ({_get_email_timezone().key})")

    # Datetime used only for the human-readable heading. Anchored to noon of the
    # day being REPORTED ON (never the wall-clock date at run time), so a 00:31
    # run delivering the previous evening's slot still prints that day's date.
    # Both the nightly and backfill paths resolve a concrete day, so this is
    # unconditional. "Generated at" below deliberately uses the real clock —
    # that line documents when the run happened, which is a different fact.
    _y, _m, _d = (int(x) for x in today.split("-"))
    label_local = datetime(_y, _m, _d, 12, 0, tzinfo=_get_email_timezone())

    # Headline Skill Vault tally (optional; never breaks the email if it fails).
    vault_line = fetch_skill_vault_tally(g, today)

    owner_repos: dict[str, dict[str, list[str]]] = defaultdict(dict)
    repo_urls: dict[str, str] = {}

    repos = list(user.get_repos(affiliation="owner,organization_member"))
    print(f"Found {len(repos)} repositories")

    for repo in repos:
        if repo.archived:
            continue

        commits = fetch_commits_with_retry(repo, since, user.login, until=until)
        if commits:
            messages = [c.commit.message for c in commits]
            owner, repo_name = repo.full_name.split("/", 1)
            owner_repos[owner][repo_name] = messages
            repo_urls[repo.full_name] = repo.html_url
            print(f"  {repo.full_name}: {len(commits)} commits")

    # No commits — return minimal result
    if not owner_repos:
        msg = "No commits today — well rested! ✅"
        vault_html = markdown_lib.markdown(vault_line) if vault_line else ""
        footer = (
            "<p>Daily Work Summary initially created by "
            '<a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>'
            '<p>Contribute to the public repository at: '
            '<a href="https://github.com/zero2webmaster/daily-work-summary">github.com/zero2webmaster/daily-work-summary</a></p>'
            f'<p style="font-size: 14px; color: #666;">Need to change the timing or timezone of these emails? '
            f'<a href="{SCHEDULE_DOCS_URL}">Click here</a> for instructions.</p>'
        )
        html = (
            f'{summary_stamp(today)}'
            f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">'
            f'<p>{msg}</p>{vault_html}{footer}</div>'
        )
        markdown_out = msg + (f"\n\n{vault_line}" if vault_line else "")
        return {
            "html": html,
            "markdown": markdown_out,
            "date": today,
            "total_commits": 0,
            "total_repos": 0,
            "repos": [],
            "ai_summaries_text": "",
            "has_commits": False,
        }

    total_commits = sum(
        len(msgs) for per_owner in owner_repos.values() for msgs in per_owner.values()
    )
    total_repos = sum(len(r) for r in owner_repos.values())

    lines = [
        f"# Daily Work Summary — {label_local.strftime('%a %b %d, %Y')}",
        "",
        f"**{total_commits} commits** across **{total_repos} repos**",
    ]
    if vault_line:
        lines += ["", vault_line]
    lines += [
        "",
        "---",
        "",
    ]

    structured_repos: list[dict[str, Any]] = []
    ai_summary_bullets: list[str] = []
    collapsed_repos = get_collapsed_repos()

    for owner in sorted(owner_repos.keys()):
        repos_data = owner_repos[owner]
        sorted_repos_list = sorted(
            repos_data.items(), key=lambda x: len(x[1]), reverse=True
        )

        lines.append(f"## {owner}")
        lines.append("")

        for repo_name, messages in sorted_repos_list:
            full_name = f"{owner}/{repo_name}"
            count = len(messages)
            commit_label = f"{count} commit{'s' if count != 1 else ''}"

            # Coordination bookkeeping: one line, no bullets, no AI call. Still
            # counted in the totals and still written to Airtable in full.
            if repo_name in collapsed_repos:
                lines.append(
                    f"**{repo_name}:** {count} coordination "
                    f"commit{'s' if count != 1 else ''}"
                )
                lines.append("")
                structured_repos.append({
                    "full_name": full_name,
                    "url": repo_urls.get(full_name, f"https://github.com/{full_name}"),
                    "owner": owner,
                    "commits": count,
                    "messages": messages,
                    "ai_summary": None,
                })
                print(f"  {full_name}: collapsed ({count} coordination commits)")
                continue

            ai_summary = generate_ai_repo_summary(messages)
            lines.append(f"### {repo_name} ({commit_label})")
            if ai_summary:
                lines.append(f"*{ai_summary}*")
                ai_summary_bullets.append(f"- {repo_name}: {ai_summary}")
            lines.append("")

            for msg in messages:
                bullet = truncate(msg)
                lines.append(f"* {bullet}")

            lines.append("")

            structured_repos.append({
                "full_name": full_name,
                "url": repo_urls.get(full_name, f"https://github.com/{full_name}"),
                "owner": owner,
                "commits": count,
                "messages": messages,
                "ai_summary": ai_summary,
            })

    lines.append("---")
    lines.append("")
    lines.append("Daily Work Summary initially created by [Zero2Webmaster Founder Dr. Kerry Kriger](https://zero2webmaster.com/kerry-kriger)")
    lines.append("")
    lines.append("Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary")
    lines.append("")
    lines.append(
        f"Need to change the timing or timezone of these emails? "
        f"[Click here]({SCHEDULE_DOCS_URL}) for instructions."
    )
    lines.append("")
    lines.append(
        f"*Covers {label_local.strftime('%a %b %d, %Y')} · "
        f"generated {_now_local().strftime('%Y-%m-%d %H:%M %Z')}*"
    )
    lines.append("")

    markdown_body = "\n".join(lines)
    html_content = markdown_lib.markdown(markdown_body, extensions=["nl2br"])
    html = (
        f'{summary_stamp(today)}'
        f'<div style="font-size: {HTML_FONT_SIZE}; line-height: 1.6;">{html_content}</div>'
    )

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

    # Time-of-day guard: when fired from a recurring cron, only proceed if
    # the current local time is inside the configured send window. Manual
    # workflow_dispatch runs bypass the guard (so admins can always trigger
    # a one-off send from the Actions UI).
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    force_run = os.environ.get("FORCE_RUN", "").strip().lower() in {"1", "true", "yes"}
    backfill = bool((os.environ.get("BACKFILL_DATE") or "").strip())

    if event_name == "workflow_dispatch" or force_run or backfill:
        why = "BACKFILL" if backfill else (event_name or "FORCE_RUN")
        print(f"Manual run ({why}) — bypassing time-of-day guard + per-day idempotency")
    else:
        allowed, reason = should_run_now()
        print(f"Time-of-day guard: {reason}")
        if not allowed:
            print("Skipping this run — not inside the configured send window.")
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("should_run=false\n")
                    fh.write("send_email=false\n")
                    fh.write("has_summary=false\n")
            return

        # Idempotency: at most one scheduled summary per local day. The send
        # window is intentionally wide to survive GitHub's throttled scheduler,
        # so several cron runs can fall inside it on the same day — without this
        # guard they would each generate and email a duplicate. The summary file
        # is committed back to the repo, so a later run on the same day sees it
        # on checkout and bows out here. Manual runs (handled above) always run.
        #
        # Keyed on the REPORTED day (_target_local), matching the filename that
        # _resolve_window/main will actually write. Keying it on the wall-clock
        # date instead would let the 00:31 and 04:31 runs both pass this guard
        # on the same morning — they'd write the same file and send two emails.
        #
        # An existing file only counts as "already sent" if it carries this
        # slot's provenance stamp. Legacy files (written before v1.11.0) are
        # named for the day the cron RAN, not the day they cover, so treating
        # their mere existence as proof would suppress the first correctly-dated
        # email for that date. Regenerating over one is the intended repair.
        slot_date = _target_local().date().isoformat()
        existing = Path(SUMMARY_DIR) / f"daily-summary-{slot_date}.md"
        stamped = False
        if existing.exists():
            try:
                stamped = summary_stamp(slot_date) in existing.read_text()
            except OSError as e:
                print(f"WARNING: could not read {existing} ({e}) — regenerating.")
            if not stamped:
                print(f"{existing} exists but is not stamped for {slot_date} "
                      "(pre-v1.11.0 misdated file) — regenerating it.")
        if stamped:
            print(f"Summary for {slot_date} already exists ({existing}) — "
                  "skipping to avoid a duplicate send.")
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("should_run=false\n")
                    fh.write("send_email=false\n")
                    fh.write("has_summary=false\n")
            return

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

    # Write summary file (always, for the archive and email step)
    Path(SUMMARY_DIR).mkdir(exist_ok=True)
    summary_path = Path(SUMMARY_DIR) / f"daily-summary-{summary_data['date']}.md"
    summary_path.write_text(summary_data["html"])
    print(f"Summary written to: {summary_path}")

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
            fh.write("should_run=true\n")
            fh.write(f"send_email={'true' if send_email else 'false'}\n")
            fh.write(f"local_date={summary_data['date']}\n")
            fh.write(f"summary_file={summary_path.as_posix()}\n")
            fh.write(f"has_summary={'true' if summary_data['has_commits'] else 'false'}\n")

    print(f"\n{'=' * 50}")
    print(summary_data["html"])


if __name__ == "__main__":
    main()
