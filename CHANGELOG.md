# Changelog

All notable changes to this project will be documented in this file.

## [1.5.0] - 2026-03-31

### Changed
- Daily summary format now matches automation requirements:
  - Per-repo conversational summary with **3-5 bullets** (features, fixes, refactors, accomplishments)
  - Repos sorted globally by commit count (most active first)
  - No-work fallback set to: **"No work today – hope you enjoyed the rest!"**
- Archive file path changed from `summaries/daily-summary-YYYY-MM-DD.md` to root-level:
  - `YYYY-MM-DD-GitHub-Daily-Summary.md`
- Email body source changed to a temp HTML file:
  - `.tmp/daily-summary-email-YYYY-MM-DD.html`
- Email subject changed to:
  - `Daily Cursor Work - YYYY-MM-DD`

### Improved
- Local automation resilience: when `PAT_GITHUB` is missing, `generate_summary.py` now attempts a `gh auth token` fallback for authenticated local runs.

### Documentation
- Updated directive (`directives/generate_daily_summary.md`) for new output format, file naming, and subject line.
- Updated `.cursorrules` expected archive filename and no-work message.
- Updated `README.md` archive format references and bumped version metadata to `1.5.0`.

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
