# Changelog

All notable changes to this project will be documented in this file.

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
