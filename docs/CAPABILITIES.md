<!-- capabilities-inventory v1 -->
**Checked against:** v2.1.1 · 2026-11-16

# What Daily Work Summary does

A plain-English list of everything this app does, so a move plan, an audit or a marketing plan cannot miss a feature. Add to it in the same commit as each new feature, and change an entry's status when the feature changes.

Each entry reads: **Name.** What it does. Status. [code]

Status words: **live** (running now), **built, off** (in the code, not switched on here), **built, waiting** (in the code, waiting on something outside it), **planned** (not built). Nothing below "live" is available today.

`execution/test_capabilities.py` fails if a setting or workflow the code uses is not named on this page, or if a `[code]` link points at a file that does not exist.

---

## For Kerry (the person who gets the email)

- **Nightly work email.** Every night around 23:00 Eastern, emails a summary of the day's commits across every repo Kerry owns or belongs to, grouped by account and then by repo, one bullet per commit. Live. [code](../.github/scripts/generate_summary.py)
- **One-sentence summary per repo.** An AI writes a short plain-English sentence above each repo's bullets saying what the work was about. Works with OpenRouter, Anthropic, Gemini or OpenAI (`AI_PROVIDER`, with `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` or `GEMINI_API_KEY`, `OPENAI_API_KEY`); picks the first key it finds if no provider is named. Live. [code](../.github/scripts/generate_summary.py)
- **"More info needed for a summary" instead of questions.** When commits say too little for a summary, the line says so rather than asking Kerry for more detail. Live. [code](../.github/scripts/generate_summary.py)
- **Version number first on each bullet.** Each bullet starts with the version the commit shipped, taken from the subject, a `Version:` line in the commit, or the repo's `VERSION` file at that commit. Bullets are cut at 85 characters. Live. [code](../.github/scripts/generate_summary.py)
- **Phone (cloud-session) work counted.** Commits made from Claude Code sessions started on Kerry's phone are counted alongside his own (`EXTRA_COMMIT_AUTHORS`, default `noreply@anthropic.com`; `none` turns it off). Live. [code](../.github/scripts/generate_summary.py)
- **Same work across many repos folded into one line.** When one change lands in several repos at once, it shows as "Across N repos" with the repo list instead of N separate sections (`ROLLUP_MIN_REPOS`, default 2). Live. [code](../.github/scripts/generate_summary.py)
- **Coordination bulletin shown as one line.** Agent bookkeeping in `z2w-agent-coordination` shows as a commit count plus one theme sentence, not dozens of bullets (`COLLAPSE_REPOS`; `none` shows full detail). Live. [code](../.github/scripts/generate_summary.py)
- **Skill Vault headline.** The email opens with how many skills were created and improved that day and the running total, with an "as of" date when the stats are old (`SKILL_VAULT_TALLY` turns it off). Live. [code](../.github/scripts/generate_summary.py)
- **Dated by the day the work happened.** A summary is labelled with the day it covers, even when GitHub runs the job after midnight. Live. [code](../.github/scripts/generate_summary.py)
- **Never sent twice.** If tonight's summary is already saved, later runs the same night stop without sending again. Live. [code](../.github/scripts/generate_summary.py)
- **Large, readable text.** The email body uses 18px text. Live. [code](../.github/scripts/generate_summary.py)
- **Settings link in every email.** The footer links to instructions for changing the send time and time zone. Live. [code](../.github/scripts/generate_summary.py)

## For anyone running their own copy (the public template)

- **Choose the send time and time zone without editing code.** `EMAIL_SEND_HOUR`, `EMAIL_SEND_MINUTE`, `EMAIL_SEND_WINDOW_MIN` and `EMAIL_TIMEZONE` set when the email goes out, in local time. Live. [code](../.github/scripts/generate_summary.py)
- **Choose where it is delivered.** `DELIVERY_METHOD` takes a comma-separated list of `email`, `slack`, `discord`, or `none` (save to the archive only). Old `airtable` and `both` values still send the email. Live. [code](../.github/scripts/generate_summary.py)
- **Email by Gmail.** Sent through Gmail with an app password (`EMAIL_USERNAME`, `EMAIL_PASSWORD`). Live. [code](../.github/workflows/daily-summary.yml)
- **Slack delivery.** Posts the summary to a Slack channel (`SLACK_WEBHOOK_URL`). Built, off: no Slack channel is connected for Kerry. [code](../.github/scripts/webhook_client.py)
- **Discord delivery.** Posts the summary to a Discord channel (`DISCORD_WEBHOOK_URL`). Built, off: no Discord channel is connected for Kerry. [code](../.github/scripts/webhook_client.py)
- **Reads every repo the owner can see.** One GitHub token (`PAT_GITHUB`) covers personal and organization repos. Live. [code](../.github/scripts/generate_summary.py)
- **Run it now button.** The "Daily Work Summary" workflow can be started by hand from GitHub, skipping the time check. Live. [code](../.github/workflows/daily-summary.yml)
- **Rebuild past days.** The "Backfill Summaries" workflow rewrites the archive for a date range (`BACKFILL_DATE` per day) without sending anything. Live. [code](../.github/workflows/backfill-summaries.yml)

## Keeping it reliable

- **Missed-email alarm.** After each real send, pings an Uptime Kuma monitor (`UPTIME_KUMA_PUSH_URL`); if a night is missed, the monitor alerts. Live. [code](../.github/workflows/daily-summary.yml)
- **Extra start times near 23:00.** Several scheduled starts around 23:10–23:40 Eastern, plus a queue so two runs never send at once. Live. [code](../.github/workflows/daily-summary.yml)
- **Automatic tests.** The "Tests" workflow runs every test suite on each change and fails if it finds none. Live. [code](../.github/workflows/tests.yml)

## For other apps

- **Daily archive on GitHub.** Every summary is saved as `summaries/daily-summary-YYYY-MM-DD.md`, stamped with the day it covers. The command center (agents.z2w.us) reads these. Live. [code](../.github/scripts/generate_summary.py)
- **Monthly portfolio size report.** On the 1st of each month the "Portfolio Stats" workflow measures every repo's lines of code, documentation and data, and saves `stats/portfolio-YYYY-MM.json` in the coordination repo for agents.z2w.us/portfolio (`STATS_MONTH` overrides the month, `PORTFOLIO_STATS_OUTPUT` sets the file path). Live. [code](../.github/scripts/portfolio_stats.py)

## Retired or paused

- **Airtable copy of each summary.** Removed in v2.0.0 (2026-10-31) at Kerry's request; nothing read it. Not available.
- **Session-engagement report.** A Claude Code hook that reports how many messages Kerry sent and questions he answered in a session. Built, off: Kerry switched it off on 2026-09-23 and asked that it not be turned back on without asking him. [code](../execution/session_metrics.py)
- **Outside timer for exact 23:00 delivery.** A Cloudflare Worker that would start the job on time. Planned, shelved: approved 2026-10-15, not needed while GitHub delivers 23:16–23:31 Eastern.
