# Directive: Generate Daily Work Summary

**Version:** 1.4.0
**Last Updated:** 2026-06-18
**Owner:** Kerry Kriger

---

## Goal

Generate a smart daily summary of all GitHub commits across every zero2webmaster and personal repository from the last 24 hours. Deliver via email, Airtable, Slack, and/or Discord, and save a Markdown archive.

## Trigger

- **Automated:** GitHub Actions cron `5 * * * *` (nominally hourly at `:05` UTC). The Python script's `should_run_now()` time-of-day guard reads `EMAIL_TIMEZONE` + `EMAIL_SEND_HOUR` + `EMAIL_SEND_MINUTE` + `EMAIL_SEND_WINDOW_MIN` Action variables and skips runs outside the configured local send window. This replaces the previous "edit-the-cron-line-in-YAML" approach so admins never touch UTC math or daylight-saving offsets.
  - **GitHub does NOT honor the hourly schedule for this repo.** Its free scheduler is heavily throttled — actual runs land every 2–5 hours, and there is a reliable dead zone from roughly **00:30–04:30 ET (≈04:30–08:30 UTC)** where it fires nothing. The runs it *does* fire most consistently are early morning ET (~00:40–02:00 ET). The guard is built around this reality (wide window + most-recent-past anchoring), not around the cron firing on time. **Do not narrow `EMAIL_SEND_WINDOW_MIN` back toward 60** expecting an on-the-minute send — that is what broke v1.5.0→1.5.1 (no summary June 5–17, fixed in v1.5.2).
- **Manual:** GitHub Actions → "Run workflow" button. `workflow_dispatch` runs bypass the time-of-day guard (so a one-off send always fires).
- **Backfill (recovery):** the separate `Backfill Summaries` workflow (`workflow_dispatch` with `start_date`/`end_date`) regenerates summaries for a past range from git history. Sets `BACKFILL_DATE=YYYY-MM-DD` per day → the script summarizes that whole local calendar day (`[00:00, 23:59:59]` in `EMAIL_TIMEZONE`, a closed window). Forces `DELIVERY_METHOD=airtable` (archive + Airtable only — never email/Slack/Discord), sends no heartbeat ping, and relies on Airtable's per-date duplicate detection so re-runs are safe. Use after an outage where the cron skipped days.
- **Timezone:** `EMAIL_TIMEZONE` variable (Settings → Actions → Variables). IANA format (e.g. `America/New_York`, `Europe/London`). [Full list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). Default: `America/New_York`. Now controls ALL date labels: subject date, markdown heading, filename in `summaries/`, "Generated at" footer timestamp, commit message, AND the scheduling guard. Previously controlled only subject + footer.
- **Send time:** `EMAIL_SEND_HOUR` (0–23, default `22`) and `EMAIL_SEND_MINUTE` (0–59, default `30`) — local target in `EMAIL_TIMEZONE`. Default = 10:30 PM in `America/New_York`.
- **Window:** `EMAIL_SEND_WINDOW_MIN` (default `480` = 8h) — minutes AFTER the target during which a delayed cron still counts. One-sided: never fires earlier than the target, and the target is anchored to the most recent PAST occurrence of HH:MM (so a run after midnight measures its lateness against last night's target, not tonight's). The 8h default is deliberately wide to survive GitHub's throttled scheduler and its 00:30–04:30 ET dead zone. **Idempotency:** at most one scheduled summary per local day — if `summaries/daily-summary-<local-date>.md` already exists on checkout, a later same-day run bows out instead of double-sending. Manual `workflow_dispatch` runs bypass both the window and the idempotency check.

## Inputs

| Input | Source | Notes |
|-------|--------|-------|
| GitHub PAT | `PAT_GITHUB` secret | Scopes: `repo`, `read:user` |
| Email credentials | `EMAIL_USERNAME`, `EMAIL_PASSWORD` secrets | Gmail App Password |
| Time window | Last 24 hours from run time | Uses `datetime.now(timezone.utc) - timedelta(hours=24)` |
| Scheduling target | `EMAIL_TIMEZONE` + `EMAIL_SEND_HOUR` + `EMAIL_SEND_MINUTE` + `EMAIL_SEND_WINDOW_MIN` variables | All four have defaults — see Trigger section |
| Delivery method | `DELIVERY_METHOD` variable | Comma-separated: `email` (default), `airtable`, `slack`, `discord`. `both` = `email,airtable` |
| Skill Vault tally | `SKILL_VAULT_TALLY` variable (default on) | Set `false` to hide the headline Skill Vault line. Reads `stats/skill-vault.json` from the coordination repo via `PAT_GITHUB` — no extra secret. See Step 3a |
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

### Step 0: Time-of-Day Guard (cron only)
- `main()` reads `GITHUB_EVENT_NAME`. If `workflow_dispatch` (manual) or `FORCE_RUN=true`, skip the guard.
- Otherwise call `should_run_now()`: returns `(allowed, reason)` based on `EMAIL_TIMEZONE` + `EMAIL_SEND_HOUR` + `EMAIL_SEND_MINUTE` + `EMAIL_SEND_WINDOW_MIN`. Target is anchored to the most recent PAST occurrence of HH:MM (steps back a day when now < today's target) so early-morning throttled runs measure lateness correctly.
- If allowed, then a per-day idempotency check: if `summaries/daily-summary-<local-date>.md` already exists, skip too (prevents the wide window from double-sending on a second same-day run).
- If not allowed (or already sent today): write `should_run=false`, `send_email=false`, `has_summary=false` to `$GITHUB_OUTPUT` and exit cleanly. Workflow's downstream steps (subject-date, commit, email) all gate on `steps.summary.outputs.should_run == 'true'`.

### Step 3: Generate Smart Summary
- Group commits by repository owner (account)
- Account header: `## owner` (e.g., `## zero2webmaster`)
- Repo header: `### repo-name` (repo name only, not full owner/repo)
- Sort repos by commit count (most active first)
- Optional AI summary: If any AI key set (OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY), generate one-sentence description per repo. Use AI_PROVIDER variable to choose: openrouter, anthropic, gemini, openai. Auto-detects from first available key if unset.
- Format each repo section:
  ```
  ### repo-name
  *AI summary sentence* (if OPENAI_API_KEY set)
  **N commits**
  * commit message 1
  * commit message 2
  ...
  ```
- One bullet per commit; show all commits (no truncation)
- Truncate individual commit messages to 80 characters
- If zero commits across all repos: "No commits today — well rested! ✅"

### Step 3a: Skill Vault tally (headline stat) — added v1.8.0
- After the date is resolved, read the pre-computed `stats/skill-vault.json` artifact (schema `skill-vault-stats/v1`) from the `zero2webmaster/z2w-agent-coordination` repo using the existing `PAT_GITHUB` client (`fetch_skill_vault_tally()`). No new secret — `PAT_GITHUB`'s org read already covers it.
- Emit a one-line headline near the top of the email (both the has-commits and no-commits paths): `🧠 **Skill Vault:** {created} created, {improved} improved today · {total} skills total`, taken from `by_day[today]` (`created`/`improved`) + `totals.skills`.
- **Staleness:** the artifact only refreshes at a Vault session-end, so when `by_day` has no entry for today the line shows just the running total + `*(Vault stats as of {as_of})*`, never an implied "0 created today".
- **Must never break the email.** `fetch_skill_vault_tally()` is fully exception-wrapped — a missing/unreadable/malformed artifact (or a fork that has none) silently drops the line and the digest sends normally.
- **Toggle:** optional `SKILL_VAULT_TALLY` Action variable (default on); set to `false` to hide the line without a code change.
- Formatting is isolated in the pure `format_skill_vault_tally(stats, today)` and covered by `.tmp/test_skill_vault_tally.py` (9/9).

### Step 4: Save Markdown Archive
- Write to `summaries/daily-summary-YYYY-MM-DD.md`
- Git add + commit + push from within the workflow

### Step 5: Deliver Summary
Based on `DELIVERY_METHOD` variable (comma-separated list, e.g. `email,slack`):

**Email** (when `email` is in the list):
- Use `dawidd6/action-send-mail` GitHub Action
- To: kerry@zero2webmaster.com
- Subject: `Daily Work Summary — Day Mon DD`
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

### Step 6: Heartbeat (dead-man's-switch) — added v1.6.0
- Final workflow step pings an Uptime Kuma **Push** monitor via `curl` to the `UPTIME_KUMA_PUSH_URL` secret. This is the prevention companion to the v1.5.2 outage fix — it makes a silent non-delivery VISIBLE. See Skill Vault `scheduled-job-liveness` ("monitor the outcome, not the schedule").
- **Fires only on the day's real run AND only if every prior step succeeded** (`if: success() && steps.summary.outputs.should_run == 'true'`). So a silent skip (guard never fires), a crash, or a failed email send all WITHHOLD the ping → the monitor alerts in hours, not a week. No-op skipped runs and quiet/no-commit days (`should_run=false`) correctly do not ping.
- **Safe before setup:** if `UPTIME_KUMA_PUSH_URL` is unset, the step no-ops (`exit 0`) — ships dark until Kerry creates the Push monitor and adds the secret.
- **Setup (one-time):** Uptime Kuma → add a **Push** monitor (heartbeat interval ~36h to tolerate GitHub's fire-time drift while still catching a missed day) → copy its push URL → save as repo secret `UPTIME_KUMA_PUSH_URL`. The job appends `?status=up&msg=daily-summary-<date>` to the base `…/api/push/<token>` URL.

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Email | kerry@zero2webmaster.com | HTML (when `email` in DELIVERY_METHOD) |
| Archive | `summaries/daily-summary-YYYY-MM-DD.md` | Markdown (always) |
| Airtable | Daily Summaries + Repositories tables | Structured records (when `airtable` in DELIVERY_METHOD) |
| Slack | Slack channel | Block Kit message (when `slack` in DELIVERY_METHOD) |
| Discord | Discord channel | Rich embed (when `discord` in DELIVERY_METHOD) |
| Logs | GitHub Actions run logs | Plaintext |

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No commits in 24h | "No commits today — well rested! ✅" |
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
