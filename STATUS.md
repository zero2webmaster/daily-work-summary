# Daily Work Summary - Project Status

**Last Updated:** 2026-06-18 (v1.8.0)

---

## 🚧 Blockers

None currently.

---

## 🧭 Decisions

### Decision: Use GitHub Actions (not local cron)
**Date:** 2026-03-11
**Rationale:** GitHub Actions provides free compute, automatic secret management, and built-in git access. No need to maintain a server or local machine running 24/7.

### Decision: Gmail SMTP via `dawidd6/action-send-mail`
**Date:** 2026-03-11
**Rationale:** Battle-tested GitHub Action for email. Gmail App Passwords provide secure auth without OAuth complexity. Supports HTML formatting for rich summaries.

### Decision: Archive summaries in `summaries/` directory
**Date:** 2026-03-11
**Rationale:** Git-committed markdown files provide a permanent, searchable history of daily work. Workflow auto-commits after each run.

### Decision: Raw `requests` for Airtable client (not `pyairtable`)
**Date:** 2026-03-11
**Rationale:** Mirrors the PHP class pattern from z2w-ai-suite, avoids adding a new dependency (`requests` is already a transitive dep of PyGithub), gives full control over error handling and retry logic.

### Decision: IDs-only for Airtable references
**Date:** 2026-03-11
**Rationale:** Using `appXXX`/`tblXXX` IDs instead of names means users can rename tables/bases in the Airtable UI without breaking the integration. Consistent with AGENTS.md best practices.

### Decision: `DELIVERY_METHOD` variable with `email` default
**Date:** 2026-03-11
**Rationale:** Backward compatible — existing users see no change. Airtable is purely opt-in via setting the variable to `airtable` or `both`.

### Decision: Comma-separated DELIVERY_METHOD for Slack/Discord
**Date:** 2026-03-11
**Rationale:** Allows any combination of channels without combinatorial explosion of named values (e.g. `email,slack,discord`). The `both` alias is preserved for backward compat. Unknown values are warned-and-dropped rather than erroring, so adding new methods in future is non-breaking.

---

## ✅ Next Actions

1. Configure Airtable: Create base, run `setup_airtable.py`, add secrets/variables
2. Test with `DELIVERY_METHOD=both` via manual workflow run
3. Test Slack delivery: add `SLACK_WEBHOOK_URL` secret, set `DELIVERY_METHOD=slack`
4. Test Discord delivery: add `DISCORD_WEBHOOK_URL` secret, set `DELIVERY_METHOD=discord`

---

## 🔧 Tech Debt

- Version drift existed (VERSION=1.2.6, README=1.2.3) — fixed in v1.3.0

---

## 📊 Recent Updates

### Session: 2026-06-18 - Skill Vault tally in the daily email (v1.8.0)
- **v1.8.0 — headline Skill Vault stat in the email.** Each digest now leads with `🧠 Skill Vault: X created, Y improved today · N skills total`, the created-vs-improved split + running total. Fulfills the no-urgency bulletin ask from `z2w-skill-vault` (2026-06-16).
- **Data source:** reads the pre-computed `stats/skill-vault.json` (schema `skill-vault-stats/v1`) from the `z2w-agent-coordination` repo via the existing `PAT_GITHUB` — **no new secret**, no second clone, no direct dependency on the private skill-vault repo.
- **Cannot break the email:** the fetch is fully exception-wrapped — missing/unreadable/malformed artifact (or a fork without it) silently drops the line. Honest about staleness: when the artifact has no entry for today it shows the running total + `(Vault stats as of YYYY-MM-DD)` rather than implying "0 created today".
- New optional `SKILL_VAULT_TALLY` Action variable (default on) hides the line without a code change.
- **Verified:** offline unit test `.tmp/test_skill_vault_tally.py` 9/9 + live render against the real artifact (`28 skills total`; created/improved split renders on matching days). py_compile + both workflow YAMLs valid.
- **Next:** remaining no-urgency ask is the monthly portfolio-stats artifact (write `stats/portfolio-YYYY-MM.json` into the coordination repo).

### Session: 2026-06-18 - Email-outage fix + dead-man's-switch + backfill (v1.5.2 → 1.7.0)
- **v1.5.2 — fixed the week-long outage.** Root cause was the time-of-day guard, NOT the email credential or an auto-disabled workflow. Two bugs skipped every run since June 5: (1) the 22:30 ET + 60-min window maps to 02:30–03:30 UTC, which sits in GitHub's scheduled-cron dead zone (it reliably fires nothing ~00:25–04:39 UTC); (2) the target was computed as *today's* 22:30, so the early-morning runs GitHub does fire measured lateness against a future target → always "too early, skip." Fix: anchor target to most-recent-past HH:MM, widen default window 60→480 min, add per-day idempotency. Verified by a clock-frozen guard test (`.tmp/test_guard.py`) 7/7.
- **v1.6.0 — dead-man's-switch heartbeat.** Workflow now pings an Uptime Kuma Push monitor after a successful run, gated `if: success() && should_run=='true'` so a skip/crash/failed-send all withhold the ping. **Verified live:** manual run's heartbeat step got `{"ok":true}` from Kuma. Secret `UPTIME_KUMA_PUSH_URL` is set.
- **v1.7.0 — backfill.** New `BACKFILL_DATE` mode (whole local calendar day) + `Backfill Summaries` workflow (start/end dates, archive + Airtable only, no email/heartbeat). **Verified:** regenerated June 6–16 → `summaries/` is now contiguous June 5→18, and Airtable records for those days exist with repos linked. (First run raced the nightly push; fixed with rebase-and-retry.)
- Fixed README version drift (was 1.5.0). 
- **Next:** none blocking. Optional future: Skill Vault tally in the email + the portfolio-stats artifact (no-urgency bulletin asks).

### Session: 2026-03-11 - Slack/Discord Delivery (v1.4.0)
- Built `webhook_client.py` — Slack Block Kit + Discord embed client with retry/rate-limit logic
- Added `send_to_slack()` + `send_to_discord()` in `generate_summary.py`
- Refactored `DELIVERY_METHOD` to comma-separated (e.g. `email,slack,discord`); `both` alias preserved
- Workflow: added `SLACK_WEBHOOK_URL` + `DISCORD_WEBHOOK_URL`; email condition now uses `send_email` output
- README: new Slack & Discord Integration section with step-by-step setup
- Bumped to v1.4.0

### Session: 2026-03-11 - Airtable Integration (v1.3.0)
- Built `airtable_client.py` — full Airtable REST API client with retry logic
- Built `setup_airtable.py` — one-time table creation via Meta API
- Refactored `generate_summary.py` to return structured data dict
- Added `write_to_airtable()` with duplicate detection and linked records
- Updated workflow with `DELIVERY_METHOD` routing and Airtable env vars
- Updated README with Airtable setup section, fixed version drift
- Bumped to v1.3.0

### Session: 2026-03-11 - Initial Setup (v1.0.0 → v1.2.6)
- Created complete 3-layer architecture
- Built GitHub Actions workflow with 10pm EST cron
- Built smart summary script with intelligent commit grouping
- Created README with production setup guide
- Added 4 AI providers, email formatting, fork sync docs
- All 3 core phases complete

---
