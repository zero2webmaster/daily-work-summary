# Daily Work Summary - Project Status

**Last Updated:** 2026-06-18 (v1.9.1)

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

### Session: 2026-06-18 - Portfolio-stats accuracy + faster workflow + session-metrics hook (v1.9.1)
- **True numbers fix.** First run reported `z2w-ai-suite` at 1.32M LoC; **85% was committed `.specstory` chat transcripts** (1.46M lines) + vendored libs. `portfolio_stats.py` now excludes `.specstory`/vendor/build/minified via `cloc --exclude-dir`/`--not-match-f`, and splits honestly: `loc` = programming-language code; `doc_lines` = code comments + prose/doc files (Markdown). Unit test 23/23.
  - **Separate finding to flag to Kerry:** `z2w-ai-suite` has `.specstory/` **committed** (528 files) — violates the 2026-06-15 portfolio heads-up to gitignore it (potential secret-leak surface). That's a z2w-ai-suite hygiene fix, tracked for that project's agent.
- **Faster workflow.** `portfolio-stats.yml` installs only `PyGithub`+`python-dotenv` (not the heavy AI SDKs) + Node-24 env. Next run installs in seconds.
- **Session-metrics Stop-hook prototype** `execution/session_metrics.py` — reports questions-answered (exact), actions-taken, declined/interrupted from the transcript; honest that plain approvals aren't logged. To be wired **globally** this session via `update-config`.
- **Verified end-to-end earlier:** v1.9.0 manual run succeeded, committed `stats/portfolio-2026-06.json` to the coordination repo → **confirmed `PAT_GITHUB` has write access** (no token change needed). Re-running with the v1.9.1 accuracy fix for true portfolio-wide numbers.

### Session: 2026-06-18 - Monthly portfolio-stats job (v1.9.0)
- **v1.9.0 — monthly portfolio-stats artifact.** New separate `Portfolio Stats` workflow snapshots every Z2W repo's lines-of-code + documentation/comment lines and commits `stats/portfolio-YYYY-MM.json` into the **`z2w-agent-coordination` repo** (not this repo — the command center's token is scoped there). Fulfills the last open no-urgency bulletin ask (`z2w-agent-command-center`, 2026-06-12, amended 2026-06-17).
- **How:** shallow-clones each repo, runs `cloc --json` (`code`→`loc`, `comment`→`doc_lines`), records `last_commit_date` + `active`/`archived` status, aggregates totals. Schema `portfolio-stats/v1`. Cadence `0 6 1 * *` (monthly) + manual run with optional `month` override.
- **Cannot affect the email:** it's a *separate* workflow; per-repo work is exception-wrapped (a repo that fails to measure → null counts + `error` note, never aborts); coordination-repo push uses rebase-and-retry for the multi-agent ref-lock race.
- **No new secret** — reuses `PAT_GITHUB` (needs write to the coordination repo, which it already reads for the Skill Vault tally).
- **Verified:** offline unit test `.tmp/test_portfolio_stats.py` 21/21 (cloc parser + aggregate builder incl. null metrics, archived split, empty portfolio); `py_compile` clean; both workflow YAMLs valid. New SOP `directives/generate_portfolio_stats.md`.
- **Next:** all known bulletin feature asks are now closed. No blocking work.

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

*(Earlier sessions — v1.0.0 initial build, v1.3.0 Airtable, v1.4.0 Slack/Discord, all 2026-03-11 — trimmed per the STATUS 3-4-session rule; full history in [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).)*

---
