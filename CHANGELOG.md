# Changelog

All notable changes to this project will be documented in this file.

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
