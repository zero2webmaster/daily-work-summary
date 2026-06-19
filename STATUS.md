# Daily Work Summary - Project Status

**Last Updated:** 2026-06-19 (v1.10.0)

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

### Session: 2026-06-19 - Answer Kerry's inbox Qs + AI Engine survey; messages-sent metric (v1.10.0)
- **Session-metrics report now headlines messages-sent.** Answers Kerry's 2026-06-18 inbox ask: "do we track total chats sent in to the agent by the admin?" The count already existed internally (`user_turns`) but was buried as "over N of your turns"; it's now the lead: *"you sent N message(s) to the agent and answered X question(s)…"*. Exact count — real typed admin messages only, excluding tool-results (also "user" transcript lines) and harness `isMeta`/`isSidechain` lines. Module docstring updated to document it.
- **Both copies synced.** Updated source `execution/session_metrics.py` and re-copied to the deployed global hook `~/.claude/hooks/session_metrics.py`; verified byte-identical via `diff`.
- **Verified:** new regression test `.tmp/test_session_metrics.py` 6/6 (asserts the count ignores tool-results + meta noise) + a live run against a real session transcript in both hook (JSON stdin) and CLI (path arg) modes.
- **Answered Kerry's portability question** (2026-06-18 18:56): the hook is **machine-local only** (script + wiring both under `~/.claude/`), so portable-stack/starter-kit buyers don't get it. Bundling it into the sellable kits is logged as an Open follow-up pending Kerry's go-ahead.
- **Answered the `z2w-ai-suite` "Z2W AI Engine" survey** in the coordination bulletin's `global.md`: daily-work-summary is the portfolio's strongest model-drift data point (hand-rolls a four-provider `AI_PROVIDERS` registry in `generate_summary.py`) and a pure-summarization product → it would consume the engine's model-registry + summarization slices over **HTTP service** (Python cron, no Node); hard boundary that the daily email must still send if the engine is down.
- **Next:** all known bulletin feature asks closed; only open item is the optional "bundle the session-metrics hook into the kits" follow-up.

### Session: 2026-06-18 - Portfolio-stats accuracy + faster workflow + session-metrics hook (v1.9.1)
- **True numbers fix.** First run reported `z2w-ai-suite` at 1.32M LoC; **85% was committed `.specstory` chat transcripts** (1.46M lines) + vendored libs. `portfolio_stats.py` now excludes `.specstory`/vendor/build/minified via `cloc --exclude-dir`/`--not-match-f`, and splits honestly: `loc` = programming-language code; `doc_lines` = code comments + prose/doc files (Markdown). Unit test 23/23.
  - **Separate finding to flag to Kerry:** `z2w-ai-suite` has `.specstory/` **committed** (528 files) — violates the 2026-06-15 portfolio heads-up to gitignore it (potential secret-leak surface). That's a z2w-ai-suite hygiene fix, tracked for that project's agent.
- **Faster workflow.** `portfolio-stats.yml` installs only `PyGithub`+`python-dotenv` (not the heavy AI SDKs) + Node-24 env. Next run installs in seconds.
- **Session-metrics Stop-hook prototype** `execution/session_metrics.py` — reports questions-answered (exact), actions-taken, declined/interrupted from the transcript; honest that plain approvals aren't logged. To be wired **globally** this session via `update-config`.
- **Verified end-to-end:** v1.9.0 manual run succeeded → **confirmed `PAT_GITHUB` has write access** to the coordination repo (no token change needed). The v1.9.1 re-run regenerated `stats/portfolio-2026-06.json` with true numbers: **41 repos (40 active, 1 archived) → 695,618 lines of code + 431,186 lines of documentation** (z2w-ai-suite now 115K LoC vs the bogus 1.32M). No measurement errors.
- **Session-metrics hook is LIVE globally:** `~/.claude/hooks/session_metrics.py` wired into `~/.claude/settings.json` Stop hook — fires for every session in every project (takes effect next session / after `/hooks` reload). Filed a `[→ z2w-starter-kit]` discussion ask with the LoC/doc numbers (Kerry's curiosity discussion: traditional-dev effort + famous-software comparisons).

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

*(Earlier sessions — the v1.5.2→1.7.0 outage-fix + dead-man's-switch + backfill (2026-06-18), and the v1.0.0 / v1.3.0 / v1.4.0 builds (2026-03-11) — trimmed per the STATUS 3-4-session rule; full history in [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).)*

---
