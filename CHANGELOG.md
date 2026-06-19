# Changelog

All notable changes to this project will be documented in this file.

## [1.10.0] - 2026-06-19

### Added
- **Session-metrics report now shows how many messages you sent the agent.** Answering Kerry's 2026-06-18 ask ("do we track total chats sent in to the agent during the session by the admin?"). The count was already computed internally (`user_turns`) but buried as "over N of your turns" — it's now the lead headline: *"you sent N message(s) to the agent and answered X question(s)…"*. The count is exact: it counts only real typed admin messages, excluding tool-results (which are also "user" transcript lines) and harness-injected `isMeta`/`isSidechain` lines. ([`execution/session_metrics.py`](execution/session_metrics.py))
  - Module docstring updated to document the messages-sent metric in the "what is/isn't measurable" section.
  - Deployed global hook (`~/.claude/hooks/session_metrics.py`) re-synced to match source (verified identical).
  - Verified by a regression test (`.tmp/test_session_metrics.py`, 6/6) that asserts the count ignores tool-results + meta noise, plus a live run against a real transcript in both hook and CLI modes.

## [1.9.1] - 2026-06-18

### Fixed
- **Portfolio stats now count authored source only — true numbers.** The first run reported `z2w-ai-suite` at 1.32M "lines of code"; investigation found **85% of that was committed `.specstory` AI chat transcripts** (1.46M lines), plus vendored libraries. `portfolio_stats.py` now runs `cloc` with `--exclude-dir` (`.specstory`, `node_modules`, `vendor`, build/output dirs, …) and `--not-match-f` (minified/bundled assets), and splits the per-language breakdown honestly: `loc` = code lines in programming languages, `doc_lines` = code comments **plus** prose/doc files (Markdown, etc.). Documentation no longer masquerades as code. ([`portfolio_stats.py`](.github/scripts/portfolio_stats.py))
- Unit test updated to cover the new `classify_cloc` code/doc split (`.tmp/test_portfolio_stats.py`, 23/23).

### Changed
- **Portfolio Stats workflow installs in seconds, not minutes.** It now installs only `PyGithub` + `python-dotenv` (the two packages it actually uses) instead of the full `requirements.txt` with its heavy AI SDKs, and sets the Node-24 actions env to silence the deprecation warning. ([`portfolio-stats.yml`](.github/workflows/portfolio-stats.yml))

### Added
- **Session-metrics Stop-hook prototype** ([`execution/session_metrics.py`](.github/scripts/../../execution/session_metrics.py)) — a Claude Code Stop hook that parses the session transcript and reports how much the admin engaged: questions answered (exact — `AskUserQuestion` calls), actions taken, and declined/interrupted (all exact). Plain "allow" approvals aren't recorded in the transcript, so the report says so honestly rather than inventing a count. Validated against real transcripts. Tracked in ROADMAP as a prototype pending wiring.

## [1.9.0] - 2026-06-18

### Added
- **Monthly portfolio-stats job — a size snapshot of every Z2W repo.** A new, separate workflow (**Portfolio Stats**) walks every repo, measures its lines of code and documentation/comment lines, and commits a versioned JSON artifact a dashboard can read and render. Fulfills the no-urgency bulletin ask from `z2w-agent-command-center` (filed 2026-06-12, amended 2026-06-17). ([`portfolio_stats.py`](.github/scripts/portfolio_stats.py), [`portfolio-stats.yml`](.github/workflows/portfolio-stats.yml))
  - **Where the artifact goes:** `stats/portfolio-YYYY-MM.json` **in the `zero2webmaster/z2w-agent-coordination` repo** — NOT this repo. The command center's GitHub token is scoped to the coordination repo only, so any artifact it reads must live there. This is the second artifact in that `stats/` directory (after `skill-vault.json`).
  - **What it measures:** each repo is shallow-cloned and run through [`cloc`](https://github.com/AlDanial/cloc) — `code` lines → `loc`, `comment` lines → `doc_lines` — plus `last_commit_date` (from `pushed_at`) and an `active`/`archived` status. Aggregate block carries `repo_count`, `active_repo_count`, `archived_repo_count`, `total_loc`, `total_doc_lines`. Schema `portfolio-stats/v1`.
  - **Cadence:** monthly (`0 6 1 * *`, 06:00 UTC on the 1st) plus a manual **Run workflow** button with an optional `month` (`YYYY-MM`) override.
  - **Decoupled by design.** A separate workflow from the nightly email, so it can never affect Kerry's morning digest. Per-repo work is fully exception-wrapped: a repo that fails to clone or measure is recorded with `null` counts and an `error` note rather than aborting the run. The push to the coordination repo uses rebase-and-retry (the bulletin clone is written by many agents, so a concurrent push can grab the ref lock first — the same race the v1.7.0 backfill hit).
  - **No new secret.** Reuses `PAT_GITHUB`, which must have write access to the coordination repo (it already reads it for the Skill Vault tally).
  - Verified by an offline unit test (`.tmp/test_portfolio_stats.py`, 21/21) covering the cloc parser and the aggregate builder (sorting, null metrics, archived split, empty portfolio).
  - New SOP: [`directives/generate_portfolio_stats.md`](directives/generate_portfolio_stats.md).

## [1.8.0] - 2026-06-18

### Added
- **Skill Vault tally as a headline line in the daily email.** When work was done on Kerry's portfolio-wide skill library that day, the email now leads with a one-line stat — e.g. `🧠 Skill Vault: 3 created, 5 improved today · 28 skills total` — surfacing the created-vs-improved split (the compounding-value signal) plus the running total. ([`generate_summary.py`](.github/scripts/generate_summary.py))
  - **Data source:** reads the pre-computed `stats/skill-vault.json` artifact (schema `skill-vault-stats/v1`) from the `zero2webmaster/z2w-agent-coordination` repo via the job's existing `PAT_GITHUB` — **no new secret**, no second clone, no dependency on the private skill-vault repo directly.
  - **Can never break the email.** The fetch is fully wrapped: if the artifact is missing, unreadable, or malformed, the tally is silently skipped and the digest sends as normal. Forks without the artifact simply never see the line.
  - **Honest about staleness.** The artifact only refreshes when a Vault session ends, so on a day with no recorded entry the line shows just the running total plus a *"(Vault stats as of YYYY-MM-DD)"* note instead of implying "0 created today".
  - New optional `SKILL_VAULT_TALLY` Action variable (default on) turns the line off without a code change.
  - Verified by an offline unit test (`.tmp/test_skill_vault_tally.py`, 9/9) covering both-counts, created-only, improved-only, stale-artifact, no-activity, zero-counts, and malformed-input cases.

## [1.7.0] - 2026-06-18

### Added
- **Backfill mode — regenerate summaries for past days the outage skipped.** The daily summaries are derived from git commit history, which is permanent, so the June 6–16 gap was never lost — just never rendered. New `BACKFILL_DATE=YYYY-MM-DD` env mode summarizes a **whole local calendar day** in `EMAIL_TIMEZONE` (a closed `[00:00, 23:59:59]` window), so "the summary for June 10 = everything committed on June 10" — clean, gap-free, non-overlapping coverage across a range. ([`generate_summary.py`](.github/scripts/generate_summary.py))
- **New `Backfill Summaries` workflow** ([`backfill-summaries.yml`](.github/workflows/backfill-summaries.yml)) — a `workflow_dispatch` with `start_date` / `end_date` inputs that loops the range, writing each day to the `summaries/` archive + Airtable. Deliberately scoped narrower than the nightly job: `DELIVERY_METHOD` is forced to `airtable` so a multi-week backfill **never** emails/Slacks/Discords, and it sends **no heartbeat ping** (a backfill isn't "today's run"). Airtable's existing per-date duplicate detection makes re-runs safe.

## [1.6.0] - 2026-06-17

### Added
- **Dead-man's-switch heartbeat so the email can never go dark unnoticed again.** This is the prevention companion to the v1.5.2 outage fix: the whole reason that outage lasted ~12 days is that nothing was watching whether the email actually went out. Now the workflow pings an [Uptime Kuma](https://github.com/louislam/uptime-kuma) **Push** monitor *after* the success-critical work — and crucially **only** on the day's real run *and* only if every prior step succeeded. So a silent skip (the guard never fires), a crash, or a failed email send all *withhold* the ping, and the monitor alerts within hours instead of someone noticing a week later. ([`daily-summary.yml`](.github/workflows/daily-summary.yml))
  - Gated on a new `UPTIME_KUMA_PUSH_URL` repository secret. **Safe before setup:** if the secret is unset the step no-ops, so this ships dark until Kerry creates the Push monitor and adds the URL.
  - No-op skipped runs and quiet/no-commit days (`should_run=false`) correctly do not ping, so they don't cause false alarms.
- Captured the underlying lesson portfolio-wide: extended the `scheduled-job-liveness` Skill Vault skill with a fifth silent-failure mode (a throttled scheduler firing outside a narrow time-of-day guard's window, plus the after-midnight target-math trap).

### Setup (one-time, Kerry)
- In Uptime Kuma: add a **Push** monitor (suggested heartbeat interval ~36h to tolerate GitHub's fire-time drift while still catching a missed day), copy its push URL, and save it as the repo secret `UPTIME_KUMA_PUSH_URL`.

## [1.5.2] - 2026-06-17

### Fixed
- **The daily email stopped arriving — no summary had been sent since June 5.** Two bugs in the "only send at the chosen time of day" guard combined to skip every run:
  - **GitHub runs the job too late at night.** The configured send time (10:30 PM Eastern) plus the old 60-minute grace window landed in a stretch of the night — roughly 12:30 AM to 4:30 AM Eastern — where GitHub's free scheduler reliably runs *nothing*. So the one-hour window the email was allowed to send in was never actually reached.
  - **The grace window did the wrong math after midnight.** The runs GitHub *does* fire happen in the early morning (around 12:40–2:00 AM Eastern). For those, the code measured the gap against *tonight's* 10:30 PM instead of *last night's*, getting a huge negative number, so it always concluded "too early, skip" no matter how wide the window was.
- **The fix:**
  - Measure the gap against the most recent past 10:30 PM (step back a day when we're past midnight) — so an early-morning run correctly counts as "a bit late," not "way too early." [`generate_summary.py`](.github/scripts/generate_summary.py)
  - Widen the default grace window from 60 minutes to 8 hours so a run that GitHub delays into the early morning still sends.
  - Add a one-per-day safety check: if today's summary already exists in the repo, a later run that same day bows out instead of sending a duplicate. This makes the wide window safe.
- Also corrected version drift: the README still said 1.5.0 even though VERSION was 1.5.1.

### Verification
- New guard test ([`.tmp/test_guard.py`](.tmp/test_guard.py), throwaway) freezes the clock at 7 representative times and confirms the throttled early-morning runs now send while pre-target and stale-afternoon runs don't — all 7 pass.
- Live test: a manual `workflow_dispatch` run from the Actions tab regenerates today's summary and sends the email.

---

## [1.5.1] - 2026-06-10

### Fixed
- **CRITICAL: Nightly summary cron was broken because the default Claude model had been retired.** [`.github/scripts/generate_summary.py`](.github/scripts/generate_summary.py) (line 187) defaulted to `claude-3-5-haiku-20241022` — Anthropic retired that snapshot on Feb 19, 2026, so every nightly run that fell through to the Anthropic native provider was 404ing silently. The other three provider defaults were also one major version behind. Updated all four:
  - Claude native: `claude-3-5-haiku-20241022` → `claude-haiku-4-5-20251001`
  - Claude OpenRouter: `anthropic/claude-3-5-haiku` → `anthropic/claude-haiku-4.5`
  - Gemini: `gemini-1.5-flash` → `gemini-2.5-flash`
  - OpenAI: `gpt-4o-mini` → `gpt-5-mini`
- The same model IDs are also referenced in the README's "Optional AI Secrets" table — all four updated to match.

### Verification
- `python3 -c "import ast; ast.parse(open('.github/scripts/generate_summary.py').read())"` — clean parse.
- The next scheduled cron run (or a manual `workflow_dispatch` from the Actions tab) is the live test. If it sends an email, we're back online.

---

## [1.5.0] - 2026-06-05

### Added
- **Timezone-aware scheduling:** New `EMAIL_SEND_HOUR` (default `22`), `EMAIL_SEND_MINUTE` (default `30`), and `EMAIL_SEND_WINDOW_MIN` (default `60`) Action variables let admins set the local target time for the daily email without touching cron syntax or UTC math. The workflow now fires hourly; the Python script's time-of-day guard skips the run unless local-clock time in `EMAIL_TIMEZONE` is inside the configured window. Manual `workflow_dispatch` runs bypass the guard.
- **Footer link in every email:** "Need to change the timing or timezone of these emails? Click here for instructions." Points at the public README's [Customizing the email schedule](https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule) section.
- **Onboarded to the Z2W agent coordination bulletin** at `zero2webmaster/z2w-agent-coordination`. Canonical block v0.1.8 added to `CLAUDE.md` and `AGENTS.md`; bulletin file `projects/daily-work-summary.md` scaffolded.

### Changed
- **Email date labels now reflect `EMAIL_TIMEZONE` consistently** — markdown heading, filename in `summaries/`, "Generated at" footer timestamp, commit message, and email subject all use the configured local zone (previously only the email subject was zone-aware; everything else was UTC, which caused the date to read as "tomorrow" when received late at night).
- **AI summary prompt tightened** (`generate_summary.py`): keeps yesterday's plain-English guardrails but bans invented-team filler ("The team improved…"), caps output at one short sentence, and replaces the 22-word example with a 13-word passive-theme one.
- **Workflow cron switched** from a single fixed UTC time (`0 3 * * *` = 10 PM EST) to hourly at `:05` (`5 * * * *`). Admins set the local target via Variables instead of editing the YAML.

### Migration

Existing installations: no action required if you're happy with the default (10:30 PM in `America/New_York`). To change the time or timezone, see [Customizing the email schedule](https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule) in the README — no YAML edit needed anymore.

## [1.4.0] - 2026-03-11

### Added
- **Slack integration:** Post daily summaries to Slack channels via Incoming Webhooks using Block Kit formatting (header, stats bar, per-repo sections with linked repo names, AI summaries in italics, footer)
- **Discord integration:** Post daily summaries to Discord channels via Incoming Webhooks using rich embeds (green/grey color by activity, inline commit stats, per-repo breakdown with hyperlinks)
- `webhook_client.py` — Slack and Discord webhook client with exponential-backoff retry, rate-limit handling (`Retry-After` header), and message-length truncation
- `SLACK_WEBHOOK_URL` secret support
- `DISCORD_WEBHOOK_URL` secret support
- `DELIVERY_METHOD` now accepts a **comma-separated list** of methods: `email`, `airtable`, `slack`, `discord` (e.g. `email,slack,discord`)
- `both` alias preserved for backward compatibility (`= email,airtable`)
- `send_email` output from Python script replaces raw `delivery_method` for cleaner workflow condition logic
- README: Slack & Discord Integration section with step-by-step setup for both platforms

### Changed
- `generate_summary.py`: delivery parsing moved to `parse_delivery_methods()` — unified, extensible, unknown-value-tolerant
- `generate_summary.py`: writes `send_email` boolean to `$GITHUB_OUTPUT` for the workflow email step
- Workflow email condition updated from `delivery_method != 'airtable'` to `send_email == 'true'`
- Workflow: `SLACK_WEBHOOK_URL` and `DISCORD_WEBHOOK_URL` env vars passed to generate step
- README Variables table updated with full `DELIVERY_METHOD` options and examples table

## [1.3.0] - 2026-03-11

### Added
- **Airtable integration:** Write daily summaries and repository data to Airtable with linked records
- `airtable_client.py` — lightweight Python Airtable REST API client with create, query, update, delete, and Meta API support
- `execution/setup_airtable.py` — one-time script to create Daily Summaries + Repositories tables via Airtable Meta API
- `DELIVERY_METHOD` variable: choose `email`, `airtable`, or `both` (default: `email` for backward compatibility)
- Duplicate detection: re-running the workflow won't create duplicate Airtable records
- Linked records: Daily Summaries ↔ Repositories (bidirectional — click a repo to see all days, click a day to see all repos)
- New secrets: `AIRTABLE_PAT`; new variables: `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_SUMMARIES`, `AIRTABLE_TABLE_REPOS`
- `requests` added explicitly to `requirements.txt`

### Changed
- `generate_summary.py` refactored to return structured data dict (html, markdown, repos, ai_summaries, counts) instead of just HTML
- Workflow conditionally skips email step when `DELIVERY_METHOD=airtable`
- README: Added Airtable Integration section with full setup guide

### Fixed
- Version drift: VERSION (1.2.6) and README (1.2.3) now synchronized at 1.3.0

## [1.2.6] - 2026-03-11

### Changed
- Email format: commit count moved to repo header line — `### z2w-web-events (16 commits)` — instead of a separate `**16 commits**` line below the AI summary

## [1.2.5] - 2026-03-11

### Added
- README: "Keeping your fork in sync" section with GitHub UI (Sync fork) and CLI (`git remote add upstream`) instructions
- README: Step 5 in Quick Start reminding fork users to sync periodically
- `.env` template: AI provider section with all four provider keys (commented out as examples)

### Fixed
- `.cursorrules`: `AI_PROVIDER` description now explicitly says to set ONE value, not the pipe-separated list (the full list was mistakenly used as the variable value, causing AI summaries to be silently skipped)
- Directive: Updated `generate_daily_summary.md` to document current behavior (owner grouping, per-commit bullets, AI summary format)

## [1.2.4] - 2026-03-11

### Fixed
- AI summary: added clear error message when `AI_PROVIDER` variable is set to an invalid value (e.g., the placeholder `"openrouter | anthropic | gemini | openai"` instead of a single provider name)
- AI summary: added logging for auto-detection so Actions logs show which provider was found
- AI summary: added `print()` when provider/key is found to confirm AI is active before each repo call

## [1.2.3] - 2026-03-11

### Changed
- README: Added "How AI Summaries Work" section with before/after examples and cost note
- README: Expanded AI provider table with direct links to get API keys for each provider
- README: Restructured Setup Guide — secrets table now lists all AI keys with clear *(Optional)* labels
- README: Added Variables setup table and expanded cron timezone table with more examples
- README: Changed git commit author from `github-actions[bot]` to `Daily Summary Bot`
- AI prompt: Strengthened instructions to prevent "N changes: X; Y" style outputs

## [1.2.2] - 2026-03-11

### Changed
- Removed example block from README
- `EMAIL_TIMEZONE` variable for subject date (default America/New_York)
- README: "Customize Schedule & Timezone" section with cron table and IANA timezone examples

## [1.2.1] - 2026-03-11

### Changed
- Email footer: Added attribution link to Kerry Kriger and contribute link to public repo
- OpenRouter default model: `anthropic/claude-3-5-haiku` (was openai/gpt-4o-mini)

## [1.2.0] - 2026-03-11

### Added
- **Four AI provider options:** OpenRouter, Anthropic, Gemini, OpenAI
- `AI_PROVIDER` variable (openrouter | anthropic | gemini | openai) — auto-detects from first available key if unset
- Secrets: `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` (or `GEMINI_API_KEY`)

## [1.1.0] - 2026-03-11

### Changed
- **Email subject:** Fixed literal `$(date...)` — now uses workflow step output for proper date (e.g., "Wed Mar 11")
- **Structure:** Account as section header (e.g., `## zero2webmaster`), repo name only as subheader (`### z2w-web-events`)
- **Format:** One bullet per commit; removed redundant "N changes:" prefix; show all commits (no "+N more")
- **Font size:** Email body wrapped in 18px HTML for better readability
- **AI summaries:** Optional OpenAI integration — one-sentence repo summary when `OPENAI_API_KEY` secret is set
- Output is now HTML (converted from markdown) for consistent email rendering

## [1.0.0] - 2026-03-11

### Added
- Initial project setup with 3-layer architecture
- GitHub Actions workflow (`daily-summary.yml`) with cron schedule at 10pm EST
- Smart summary script (`generate_summary.py`) with intelligent commit grouping
- Gmail SMTP email delivery via `dawidd6/action-send-mail`
- Markdown archive saved to `summaries/` directory
- Directive: `generate_daily_summary.md` (Layer 1 SOP)
- Edge case handling: no commits, long messages, PAT errors, rate limiting
- Manual workflow trigger via `workflow_dispatch`
- README with complete secret setup instructions (PAT, Gmail App Password)
