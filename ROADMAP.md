# Daily Work Summary - Project Roadmap

**Project:** Daily Work Summary
**Started:** 2026-03-11
**Goal:** Automated daily GitHub commit summaries emailed at 10pm EST

---

## Phase 1: Core GitHub Actions Workflow ✅
**Status:** Complete (2026-03-11)
**Estimated Time:** 15 minutes

**Tasks:**
- [x] Create `.github/workflows/daily-summary.yml` with cron schedule (`0 3 * * *` UTC = 10pm EST)
- [x] Configure permissions: `contents: write`
- [x] Set up Python 3.11 + PyGithub + Gmail SMTP (`dawidd6/action-send-mail`)
- [x] Add `workflow_dispatch` for manual test runs
- [x] Configure email delivery with HTML formatting

**Verification:**
```bash
# Verify workflow YAML is valid
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
# Manual trigger: Actions tab → Daily Work Summary → Run workflow
```

**Dependencies:** None (first step)

---

## Phase 2: Smart Summary Script ✅
**Status:** Complete (2026-03-11)
**Estimated Time:** 10 minutes

**Tasks:**
- [x] Create `.github/scripts/generate_summary.py`
- [x] Fetch ALL repos (zero2webmaster/* + personal) via PyGithub
- [x] Collect commits from last 24 hours per repo
- [x] Intelligent grouping: "3 changes: X; Y; Z (+2 more)"
- [x] Sort repos by commit count (most active first)
- [x] Edge cases: no commits, long messages, PAT errors, rate limiting
- [x] Output: Markdown summary file + exit code for email gating

**Verification:**
```bash
# Syntax check
python3 -m py_compile .github/scripts/generate_summary.py
# Local test (requires PAT_GITHUB env var)
PAT_GITHUB=ghp_xxx python3 .github/scripts/generate_summary.py
```

**Dependencies:** Phase 1 (workflow calls this script)

---

## Phase 3: Production Setup Guide ✅
**Status:** Complete (2026-03-11)
**Estimated Time:** 5 minutes

**Tasks:**
- [x] README.md with exact secret setup steps
- [x] PAT_GITHUB: Required scopes (`repo`, `read:user`)
- [x] EMAIL_PASSWORD: Gmail App Password creation steps
- [x] Repository permissions: "Read and write permissions"
- [x] Manual test workflow button instructions

**Verification:**
```bash
# Confirm README exists and has key sections
grep -c "PAT_GITHUB\|EMAIL_PASSWORD\|App Password" README.md
```

**Dependencies:** Phases 1-2 (documents what was built)

---

## Phase 4: Airtable Integration ✅
**Status:** Complete (2026-03-11)
**Estimated Time:** 30 minutes

**Tasks:**
- [x] Create `airtable_client.py` — Python Airtable REST API client (ID-based, modeled on PHP class)
- [x] Create `execution/setup_airtable.py` — one-time table creation via Meta API
- [x] Refactor `generate_summary.py` to return structured data + Airtable write function
- [x] Add `DELIVERY_METHOD` variable (`email`, `airtable`, `both`) with backward-compatible default
- [x] Update workflow to pass Airtable env vars and conditionally skip email
- [x] Duplicate detection (prevent re-creating records on workflow re-runs)
- [x] Linked records: Daily Summaries ↔ Repositories (bidirectional)

**Verification:**
```bash
# Syntax check all Python files
python3 -m py_compile .github/scripts/airtable_client.py
python3 -m py_compile .github/scripts/generate_summary.py
python3 -m py_compile execution/setup_airtable.py
# Verify workflow YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
```

**Dependencies:** Phases 1-3 (builds on existing summary generation)

---

## Phase 5: Slack / Discord Delivery ✅
**Status:** Complete (2026-03-11)
**Estimated Time:** 45 minutes

**Tasks:**
- [x] Create `webhook_client.py` — Slack Block Kit + Discord embed delivery with retry logic
- [x] Add `send_to_slack()` + `send_to_discord()` functions to `generate_summary.py`
- [x] Refactor `DELIVERY_METHOD` to accept comma-separated values (`email,slack,discord`)
- [x] Add `SLACK_WEBHOOK_URL` + `DISCORD_WEBHOOK_URL` secrets to workflow
- [x] Fix email step condition: script outputs `send_email=true/false` via `$GITHUB_OUTPUT`
- [x] README: Added Slack & Discord Integration section with step-by-step webhook setup
- [x] Handle message length limits (Slack 3000 chars/block, Discord 4096 char description)
- [x] Bumped to v1.4.0

**Verification:**
```bash
python3 -m py_compile .github/scripts/webhook_client.py
python3 -m py_compile .github/scripts/generate_summary.py
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
```

**Dependencies:** Phases 1-4 (builds on existing delivery routing)

---

## Reliability Hardening (2026-06-18) ✅

Prompted by a ~12-day silent email outage (no summary June 5–17).

- [x] **v1.5.2** — Fixed the time-of-day guard (anchor target to most-recent-past HH:MM + widen window 60→480 min + per-day idempotency). Root cause: GitHub's cron dead zone + after-midnight target math. Verified by clock-frozen guard test (7/7).
- [x] **v1.6.0** — Dead-man's-switch: post-run Uptime Kuma Push heartbeat, gated so a skip/crash/failed-send withholds the ping. Verified live (`{"ok":true}`).
- [x] **v1.7.0** — Backfill mode + `Backfill Summaries` workflow. Recovered June 6–16 into the archive + Airtable (archive now contiguous June 5→18).

**Verification:**
```bash
python3 -m py_compile .github/scripts/generate_summary.py
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/backfill-summaries.yml'))"
```

---

## Skill Vault Tally in the Email (2026-06-18) ✅

Fulfills the no-urgency bulletin ask from `z2w-skill-vault` (2026-06-16): surface a headline Skill Vault statistic in the daily digest.

- [x] **v1.8.0** — Email leads with `🧠 Skill Vault: X created, Y improved today · N skills total`. Reads the pre-computed `stats/skill-vault.json` (`skill-vault-stats/v1`) from the coordination repo via `PAT_GITHUB` (no new secret). Fully exception-wrapped so it can never break the email; honest "(Vault stats as of …)" note when the artifact is stale; optional `SKILL_VAULT_TALLY` Action variable to disable.

**Verification:**
```bash
source venv/bin/activate
python -m py_compile .github/scripts/generate_summary.py
python .tmp/test_skill_vault_tally.py   # 9/9
python -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
```

---

## Monthly Portfolio Stats Artifact (2026-06-18) ✅

Fulfills the no-urgency bulletin ask from `z2w-agent-command-center` (filed 2026-06-12, amended 2026-06-17): produce a versioned portfolio-stats JSON the command center can read and render.

- [x] **v1.9.0** — New `Portfolio Stats` workflow + `portfolio_stats.py`. Monthly (`0 6 1 * *`) + manual run. Shallow-clones every repo, runs `cloc` (`code`→`loc`, `comment`→`doc_lines`), records `last_commit_date` + `active`/`archived` status, aggregates totals, and commits `stats/portfolio-YYYY-MM.json` into the **`z2w-agent-coordination` repo** (not this repo — the command center's token is scoped there). Schema `portfolio-stats/v1`. Separate from the email workflow (can't affect the digest); per-repo exception-wrapped; rebase-and-retry push for the multi-agent ref-lock race; reuses `PAT_GITHUB` (no new secret). SOP: `directives/generate_portfolio_stats.md`.

**Verification:**
```bash
source venv/bin/activate
python -m py_compile .github/scripts/portfolio_stats.py
python .tmp/test_portfolio_stats.py   # 21/21
python -c "import yaml; yaml.safe_load(open('.github/workflows/portfolio-stats.yml'))"
```

---

## Session Metrics Stop Hook (2026-06-18 → 2026-06-19) ✅ Live

Kerry's idea: at the end of every session, report how much the admin had to engage — messages sent, questions answered through the official answer system, plus action/approval activity.

- [x] **Prototype built** — `execution/session_metrics.py`. A Claude Code **Stop hook** that parses the session transcript JSONL and reports: messages sent by the admin (exact — `user_turns`), questions answered (exact — `AskUserQuestion` calls), actions taken (exact — all tool calls), declined/interrupted (exact). Validated against real transcripts.
- [x] **Honest limitation documented** — plain "allow" approvals are NOT written to the transcript, so a raw approval count isn't reconstructable; the hook reports "actions taken + declined" as the closest exact proxy and says so.
- [x] **Wired up globally (v1.9.1).** Installed at `~/.claude/hooks/session_metrics.py` + a Stop-hook entry in `~/.claude/settings.json` — fires for every session in every project. Surfaces via `systemMessage` so it renders cleanly in the UI.
- [x] **Messages-sent headline (v1.10.0, 2026-06-19).** Answered Kerry's "do we track total chats sent in by the admin?" — the report now leads with *"you sent N message(s) to the agent…"*. Count was already collected; now surfaced. Regression test `.tmp/test_session_metrics.py` 6/6.
- [ ] **Optional — bundle into the sellable kits** (portable-stack / starter-kit) so licensees get it on clone (repo-relative `.claude/settings.json` + `tools/session_metrics.py`). Answered Kerry's portability question; pending his go-ahead. (See bulletin Open follow-ups.)
- [ ] **Optional polish** — write the report to a rolling log for cross-session trend tracking.

**Note:** this is a Claude Code harness feature, not part of the nightly digest pipeline — it lives here because the idea surfaced in this project's session.

**Verification:**
```bash
python3 -m py_compile execution/session_metrics.py
python3 execution/session_metrics.py ~/.claude/projects/<proj>/<session>.jsonl
```

---

## Phase: Correct Summary Dating ✅
**Status:** Complete (2026-07-31, v1.11.0)

Kerry reported twice (2026-06-23, 2026-06-27) that the daily email arrives ~12:11 AM dated that morning instead of the day it summarizes. Both reports sat un-ACK'd in the bulletin inbox; a third report on 2026-07-31 triggered this fix.

**Tasks:**
- [x] Reproduce from the live run log — `target ... (Jul 30)` vs `Local date label: 2026-07-31` in run `30604355032`
- [x] Add `_target_local()` as the single slot anchor shared by the send guard and the date label
- [x] Switch the nightly path to closed calendar-day windows, identical to backfill
- [x] Fix the email subject, which re-derived the date from a shell `date` call
- [x] Re-key the duplicate-send guard on the covered day (would otherwise double-send)
- [x] Add the `daily-summary/v2` provenance stamp so the fix deploys safely over the misdated archive
- [x] Correct README's documented send window (60 → 480, drifted since v1.5.2)
- [x] Update `directives/generate_daily_summary.md` to v1.5.0 with a "Which day a summary covers" section

**Verification:**
```bash
python3 execution/test_summary_date.py                      # 25/25 clock-frozen checks
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
```
Live end-to-end run confirmed the fix: the archive file labeled "Fri Jul 31" (157 commits/40 repos) regenerates as `daily-summary-2026-07-30.md` (160/40) — same work, correct label.

**Follow-up (needs Kerry's go-ahead):** `summaries/` files dated 2026-06-18 → 2026-07-31 remain off by one. Realigning them = a `Backfill Summaries` run over that range, which spends OpenRouter credits (~44 days x ~10 repos).

---

## Phase: Digest Signal Density ✅
**Status:** Complete (2026-08-15, v1.13.0)

Kerry filed two observations on 2026-08-14 after reading the Aug 13 email. Both were about the same thing: the digest spent its space in proportion to commit *count* rather than to how much distinct work happened.

**Tasks:**
- [x] Roll up work repeated across many repos into one line — `**Across N repos** — <subject>` plus the repo list
- [x] Restrict the rollup to single-commit repos so a section can never show a count larger than its bullet list
- [x] Exact subject-line matching only (`normalize_subject()`), never fuzzy — two different commits must never merge into one claim
- [x] Restore the one-sentence AI theme on collapsed coordination repos (the detail Kerry missed after v1.12.0)
- [x] Make both behaviours configurable (`ROLLUP_MIN_REPOS`, existing `COLLAPSE_REPOS`)
- [x] Measure the effect on Kerry's real data rather than asserting it

**Verification:**
```bash
source venv/bin/activate
python execution/run_tests.py                               # 6/6 suites, incl. 30 rollup checks
python -c "import yaml; yaml.safe_load(open('.github/workflows/daily-summary.yml'))"
```
Replaying the real `summaries/daily-summary-2026-08-13.md` archive: **52 repo sections → 13**, 39 repos folded into one rollup line, and 39 AI calls saved. Kerry named three repos in his report; the actual count was 39.

---

## Phase: Tests Runnable by Anyone but Kerry ✅
**Status:** Complete (2026-08-15, v1.13.0)

Closes the `standards.tests-tracked` **[HIGH]** finding filed by `audit-engine` (2026-08-01). The finding was correct, and understated: not only was there no CI runner, four of the five suites were sitting in the gitignored `.tmp/` directory, so they passed on Kerry's machine and did not exist in any clone.

**Tasks:**
- [x] Move `test_guard`, `test_portfolio_stats`, `test_session_metrics`, `test_skill_vault_tally` into tracked `execution/`
- [x] Verify all suites pass from the new location (they did, before and after)
- [x] Add `execution/run_tests.py` — one command shared by CI and local dev
- [x] Add the `Tests` workflow (push + PR + manual)
- [x] Assert at least one suite is present in the clone, so an empty run fails instead of passing
- [x] Document the suites in README

**Verification:**
```bash
python3 execution/run_tests.py    # 6/6 suite(s) passed
git ls-files 'execution/test_*.py' | wc -l   # 6
```

---

## Post-Core Improvements (Future)

📋 **Pending** - Implement after core is stable:

- [ ] Filter by repo patterns (WordPress vs AI projects)
- [ ] Commit impact analysis (lines changed, files touched)
- [ ] Weekly/monthly rollup summaries
- [ ] VS Code/Cursor integration (sidebar widget)

---

*Last Updated: 2026-08-15 (v1.13.0)*
