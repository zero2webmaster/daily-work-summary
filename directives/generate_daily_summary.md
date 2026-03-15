# Directive: Generate Daily Work Summary

**Version:** 1.3.0
**Last Updated:** 2026-03-15
**Owner:** Kerry Kriger

---

## Goal

Generate a smart daily summary of all GitHub commits across every zero2webmaster and personal repository from the last 24 hours. Deliver via email, Airtable, Slack, and/or Discord, and save a Markdown archive.

## Trigger

- **Automated:** GitHub Actions cron (default `0 3 * * *` UTC = 10pm EST). User edits workflow to change time.
- **Manual:** GitHub Actions → "Run workflow" button
- **Timezone:** `EMAIL_TIMEZONE` variable (e.g. America/New_York) for subject date. Default: America/New_York.

## Inputs

| Input | Source | Notes |
|-------|--------|-------|
| GitHub PAT | `PAT_GITHUB` secret | Scopes: `repo`, `read:user` |
| Email credentials | `EMAIL_USERNAME`, `EMAIL_PASSWORD` secrets | Gmail App Password |
| Time window | Last 24 hours from run time | Uses `datetime.utcnow() - timedelta(hours=24)` |
| Delivery method | `DELIVERY_METHOD` variable | Comma-separated: `email` (default), `airtable`, `slack`, `discord`. `both` = `email,airtable` |
| Airtable PAT | `AIRTABLE_PAT` secret | Required when delivery includes `airtable` |
| Airtable IDs | `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_SUMMARIES`, `AIRTABLE_TABLE_REPOS` variables | All IDs (`appXXX`, `tblXXX`), never names |
| Slack webhook | `SLACK_WEBHOOK_URL` secret | Required when delivery includes `slack` |
| Discord webhook | `DISCORD_WEBHOOK_URL` secret | Required when delivery includes `discord` |

## Process

### Step 1: Authenticate & Fetch Repos
- Authenticate with PyGithub using `PAT_GITHUB`
- Fetch ALL repos the authenticated user owns (including private)
- Skip forks (optional — currently included)

### Step 2: Collect Commits
- For each repo, query commits from last 24 hours
- Filter to commits authored by the authenticated user
- Collect: repo name, commit message (first line), SHA, timestamp

### Step 3: Generate Smart Summary
- Sort repos globally by commit count (most active first)
- Repo header format: `**repo-name** (N commits)` with `owner/repo` context
- Generate **3-5 bullets per repo** summarizing outcomes (features, refactors, bug fixes, accomplishments)
- Optional AI bullet generation: if any AI key exists, request 3-5 concise bullets from selected provider (`AI_PROVIDER`), else fallback to deterministic keyword-based summarization
- Optional AI one-sentence theme summary is still included in structured payload for downstream channels
- Output tone: concise, conversational, professional
- If zero commits across all repos: `No work today – hope you enjoyed the rest!`

### Step 4: Save Markdown Archive
- Write to `YYYY-MM-DD-GitHub-Daily-Summary.md` in repo root
- Also write HTML email payload to `.tmp/YYYY-MM-DD-GitHub-Daily-Summary.html`
- Git add + commit + push from within the workflow

### Step 5: Deliver Summary
Based on `DELIVERY_METHOD` variable (comma-separated list, e.g. `email,slack`):

**Email** (when `email` is in the list):
- Use `dawidd6/action-send-mail` GitHub Action
- To: kerry@zero2webmaster.com
- Subject: `Daily Cursor Work - YYYY-MM-DD`
- Body: HTML-formatted summary
- `generate_summary.py` outputs `send_email=true/false` to `$GITHUB_OUTPUT`; workflow email step is conditional on that value

**Airtable** (when `airtable` is in the list):
- Find or create Repository records for each repo (by full_name)
- Create Daily Summary record with all fields + linked repo records
- Duplicate detection: skip if record for today's date already exists
- All references use IDs (`appXXX`, `tblXXX`), never table/base names

**Slack** (when `slack` is in the list):
- POST to `SLACK_WEBHOOK_URL` secret
- Slack Block Kit message: header, stats bar, per-repo sections with linked names, AI summaries in italics, footer
- Message length capped at 3000 chars/block; max 50 blocks; overflows noted as "...and N more repos"

**Discord** (when `discord` is in the list):
- POST to `DISCORD_WEBHOOK_URL` secret
- Discord embed: green (has commits) or grey (no commits) accent, inline commit/repo stats, per-repo breakdown with hyperlinks
- Description capped at 4000 chars; overflows truncated with `...`

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Email | kerry@zero2webmaster.com | HTML (when `email` in DELIVERY_METHOD) |
| Archive | `YYYY-MM-DD-GitHub-Daily-Summary.md` | Markdown (always) |
| Airtable | Daily Summaries + Repositories tables | Structured records (when `airtable` in DELIVERY_METHOD) |
| Slack | Slack channel | Block Kit message (when `slack` in DELIVERY_METHOD) |
| Discord | Discord channel | Rich embed (when `discord` in DELIVERY_METHOD) |
| Logs | GitHub Actions run logs | Plaintext |

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No commits in 24h | "No work today – hope you enjoyed the rest!" |
| Long commit message | Truncate to 80 chars with `...` |
| 403 PAT error | Log clear error + link to token settings |
| Empty repo (no commits ever) | Skip silently |
| API rate limit (5000/hr) | Exponential backoff, max 3 retries |
| Archived repo | Skip (no recent commits) |
| Fork repos | Include (may want to filter later) |

## Tools/Scripts

| Script | Purpose |
|--------|---------|
| `.github/scripts/generate_summary.py` | Main summary generator + delivery routing (Layer 3) |
| `.github/scripts/airtable_client.py` | Airtable REST API client (Layer 3) |
| `.github/scripts/webhook_client.py` | Slack + Discord webhook delivery (Layer 3) |
| `.github/workflows/daily-summary.yml` | Workflow orchestration |
| `execution/setup_airtable.py` | One-time Airtable table creation |

## Performance

- Typical run: 30-60 seconds (depending on repo count)
- API calls: ~1 per repo + 1 auth call
- Rate limit budget: 5000 calls/hour (PAT), should use <100

## Monitoring

- Check GitHub Actions → "Daily Work Summary" for run history
- Failed runs trigger GitHub's built-in email notifications
- Summary archive in `summaries/` provides historical record

## Lessons Learned

*(Update this section as issues are discovered)*

- Gmail App Passwords must NOT include spaces (Google displays them formatted with spaces)
- GitHub cron schedules may be delayed up to 15-30 min during peak times
- `workflow_dispatch` is essential for testing without waiting for cron
