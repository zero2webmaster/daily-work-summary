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

## Session Metrics Stop Hook (2026-06-18) 🔬 Prototype

Kerry's idea: at the end of every session, report how much the admin had to engage — questions answered through the official answer system, plus permission/approval activity.

- [x] **Prototype built** — `execution/session_metrics.py`. A Claude Code **Stop hook** that parses the session transcript JSONL and reports: questions answered (exact — `AskUserQuestion` calls), actions taken (exact — all tool calls), declined/interrupted (exact), and user turns. Validated against real transcripts (a session with an `AskUserQuestion` reports `1 question across 1 prompt`).
- [x] **Honest limitation documented** — plain "allow" approvals are NOT written to the transcript, so a raw approval count isn't reconstructable; the hook reports "actions taken + declined" as the closest exact proxy and says so.
- [ ] **Decide scope + wire it up.** Not yet installed. Options: (a) project-local `.claude/settings.json` (fires only for sessions in this repo), or (b) global `~/.claude/settings.json` (every session, every project — likely what Kerry wants). Recommend wiring via the `update-config` skill. Snippet is in the script's docstring.
- [ ] **Optional polish** — write the report to a rolling log for trend tracking; surface it via the hook's `systemMessage` output so it renders cleanly in the UI.

**Note:** this is a Claude Code harness feature, not part of the nightly digest pipeline — it lives here because the idea surfaced in this project's session.

**Verification:**
```bash
python3 -m py_compile execution/session_metrics.py
python3 execution/session_metrics.py ~/.claude/projects/<proj>/<session>.jsonl
```

---

## Post-Core Improvements (Future)

📋 **Pending** - Implement after core is stable:

- [ ] Filter by repo patterns (WordPress vs AI projects)
- [ ] Commit impact analysis (lines changed, files touched)
- [ ] Weekly/monthly rollup summaries
- [ ] VS Code/Cursor integration (sidebar widget)

---

*Last Updated: 2026-06-18 (v1.9.0)*
