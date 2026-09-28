# Daily Work Summary - Project Status

**Last Updated:** 2026-09-28 (v1.13.1)

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

### Decision: A summary is dated by the SLOT it delivers, not the run time
**Date:** 2026-07-31 (v1.11.0)
**Rationale:** GitHub throttles cron overnight and typically fires the 23:00 ET slot around 00:30 the next morning. Dating a summary by wall-clock run time therefore names the wrong day on essentially every run — the bug Kerry reported on 2026-06-23 and again on 2026-06-27. `_target_local()` is now the single anchor both the send guard and the date label read, and the nightly path uses closed calendar-day windows identical to the backfill path. Corollary rule for future work: **never re-derive a date from `_now_local()` for labeling.**

### Decision: Stamp archive files with the day they cover
**Date:** 2026-07-31 (v1.11.0)
**Rationale:** Deploying the date fix over an archive whose filenames were already wrong would have made the first correct run see `daily-summary-2026-07-31.md` present and skip — costing a day's email silently. An inert `<!-- daily-summary/v2 covers="..." -->` comment gates the idempotency check instead of bare file existence, so legacy misdated files are regenerated rather than trusted. Also means a filename is never the only record of a file's contents.

### Decision: Roll up repeated commits only for single-commit repos
**Date:** 2026-08-15 (v1.13.0)
**Rationale:** The tempting version pulls the shared bullet out of *every* repo that landed it. That leaves a section headed "5 commits" above 4 bullets — the digest contradicting itself, which is worse than the repetition it fixes. Restricting the rollup to repos whose *only* commit is the shared one makes the invariant structural rather than remembered: a section's count always equals its bullet list. It also happens to cover the real case, because mass propagation lands exactly one commit per repo. Corollary for future work: **widen this only if you can state what keeps counts and bullets in agreement.**

### Decision: Match repeated commits exactly, never fuzzily
**Date:** 2026-08-15 (v1.13.0)
**Rationale:** Fuzzy matching would catch near-identical commits, but the cost of a false merge is asymmetric — the digest would assert that N repos did the same thing when they did not, and Kerry has no way to detect that from the email. Exact matching on the whitespace/case-normalized **subject line** (bodies carry per-repo trailers) can only ever fail by under-grouping, which is visible and harmless.

### Decision: Comma-separated DELIVERY_METHOD for Slack/Discord
**Date:** 2026-03-11
**Rationale:** Allows any combination of channels without combinatorial explosion of named values (e.g. `email,slack,discord`). The `both` alias is preserved for backward compat. Unknown values are warned-and-dropped rather than erroring, so adding new methods in future is non-breaking.

---

## ✅ Next Actions

1. **Measure the v1.13.1 send-time change around 2026-10-12.** Baseline before the change: sends landed between 23:14 and 05:28 ET (Aug 25 → Sep 28). Run `TZ=America/New_York git log --since=2026-09-29 --date=format-local:'%a %m-%d %H:%M' --format='%ad %s' -- summaries/` and compare. If there's no improvement, propose an external precise trigger to Kerry (see ROADMAP). Name the covered day, not the delivery time, when reporting (v1.11.0 rule).
2. **Session-metrics hook: ON HOLD.** Kerry turned the global Stop hook off on 2026-09-23 and asked that it not be re-added without asking him. The approved "bundle into the sellable kits as opt-in" follow-up is paused until he says it's still wanted.
3. **Kerry's call — realign the misdated June archive** (2026-06-18 → 06-30, 13 files). He chose July-only on 2026-07-31; re-open only if he asks.
4. Test Slack delivery: add `SLACK_WEBHOOK_URL` secret, set `DELIVERY_METHOD=slack`
5. Test Discord delivery: add `DISCORD_WEBHOOK_URL` secret, set `DELIVERY_METHOD=discord`

---

## 🔧 Tech Debt

- Version drift existed (VERSION=1.2.6, README=1.2.3) — fixed in v1.3.0

---

## 📊 Recent Updates

### Session: 2026-09-28 - Bulletin triage + send-time consistency (v1.13.1)

- **Kerry's 2026-09-17 question, "why is the send time so variable?", answered with data.** The workflow is scheduled hourly, but GitHub fired it only ~5–6×/day, 3–5h apart. Sends ranged 23:14–05:28 ET over the prior month. Added slot-targeted runs at 23:10/23:25/23:40 ET (EDT + EST) plus a `concurrency` group. Whether GitHub honours these better is an experiment, to be measured ~Oct 12.
- **audit-engine `standards.gitignore-entries` [HIGH] closed.** Added `.claude/settings.local.json` to `.gitignore` (never tracked; verified with `check-ignore --no-index` against a null global excludes file).
- **Kerry's 2026-08-20 question answered:** `z2w-templates` is the private repo holding the canonical Templates folder, the source of the private `@zero2webmaster/templates` package. Its "sync … refresh from working copy" commits are routine mirroring of the local Templates folder.
- **Checked, not a problem:** no Sep 7 archive file exists because Labor Day had zero commits (the run logged "No commits today"). The heartbeat's "not configured" log line is the step's script being echoed; last night's ping returned `{"ok":true}`.
- **Closed:** the v1.13.0 watch item. The theme line was live from Aug 15 and the "Across N repos" rollup has appeared in real emails (Sep 19, 22, 24).
- **Verified:** 6/6 suites; test_guard 14/14 (7 new); all 5 workflow YAMLs parse.

### Session: 2026-08-15 - Digest signal density + tests anyone can run (v1.13.0)

Worked Kerry's two unread 2026-08-14 bulletin dispatches and the HIGH audit finding.

- **Repetition rollup.** One action propagated portfolio-wide previously got a full section per repo. Now folded into `**Across N repos** — <subject>` + the repo list. **Measured on the real 2026-08-13 archive: 52 repo sections → 13**, 39 repos folded, 39 AI calls saved. Kerry reported three repeats; it was 39.
- **Kept deliberately narrow.** Only single-commit repos roll up, so a section can never show a commit count larger than its bullet list. Matching is exact on the normalized subject line — never fuzzy.
- **Collapsed coordination repos got their theme sentence back** (Kerry's other dispatch: "no longer show details"). One AI call restores the *what* without undoing the v1.12.0 collapse; `COLLAPSE_REPOS=none` still restores full bullets.
- **Audit finding closed, and it was understated.** `audit-engine` flagged "tests tracked but no runner." True — and 4 of the 5 suites were sitting in gitignored `.tmp/`, passing on Kerry's machine and absent from every clone. All 4 moved to `execution/`, plus `run_tests.py` and a `Tests` workflow that asserts suites are actually present before reporting a pass.
- **Verified:** 6/6 suites (30 new rollup checks); all 5 workflow YAMLs parse; `py_compile` clean; rollup measured by replaying real archived data rather than asserted.
- **Correction logged:** I briefly read the archive as missing Aug 13–14 and started investigating an outage. The local clone was simply two commits behind origin — the bot pushes there and nothing had pulled since. No outage; nightly runs are healthy.

### Session: 2026-07-31 - Fix the one-day-late summary date (v1.11.0)

**Reported twice by Kerry and unanswered in the bulletin inbox since June** (2026-06-23 and 2026-06-27): the email arrives ~12:11 AM and is dated that morning rather than the day it summarizes.

- **Root cause:** `should_run_now()` correctly anchored to the most recent past send slot (v1.5.2), but `_resolve_window()` independently labeled with `_now_local()` and fetched a rolling 24h window. The failing run's log shows the disagreement outright: `target 23:00 America/New_York (Jul 30)` / `Local date label: 2026-07-31`.
- **Fix:** `_target_local()` is now the single anchor for guard + label; nightly uses closed calendar-day windows matching backfill.
- **Also fixed:** the email subject was computed by a separate shell `date` call (same bug, independently); the duplicate-send guard was keyed on run date and would have double-sent once the label moved; README claimed a 60-min window vs the code's 480 since v1.5.2.
- **Transition safety:** new `daily-summary/v2` provenance stamp gates idempotency so the fix deploys over the misdated archive without swallowing a day's email.
- **Verified:** 25/25 clock-frozen checks (`execution/test_summary_date.py`); both workflow YAMLs parse; live end-to-end run reproduced the failure and confirmed the fix — the file labeled "Fri Jul 31" (157 commits/40 repos) regenerates as `daily-summary-2026-07-30.md` (160/40).
- **Open:** archive realignment for 2026-06-18 → 2026-07-31 awaits Kerry's go-ahead (paid AI calls).

### Session: 2026-06-19 - Answer Kerry's inbox Qs + AI Engine survey; messages-sent metric (v1.10.0)
- **Session-metrics report now headlines messages-sent.** Answers Kerry's 2026-06-18 inbox ask: "do we track total chats sent in to the agent by the admin?" The count already existed internally (`user_turns`) but was buried as "over N of your turns"; it's now the lead: *"you sent N message(s) to the agent and answered X question(s)…"*. Exact count — real typed admin messages only, excluding tool-results (also "user" transcript lines) and harness `isMeta`/`isSidechain` lines. Module docstring updated to document it.
- **Both copies synced.** Updated source `execution/session_metrics.py` and re-copied to the deployed global hook `~/.claude/hooks/session_metrics.py`; verified byte-identical via `diff`.
- **Verified:** new regression test `.tmp/test_session_metrics.py` 6/6 (asserts the count ignores tool-results + meta noise) + a live run against a real session transcript in both hook (JSON stdin) and CLI (path arg) modes.
- **Answered Kerry's portability question** (2026-06-18 18:56): the hook is **machine-local only** (script + wiring both under `~/.claude/`), so portable-stack/starter-kit buyers don't get it. Bundling it into the sellable kits is logged as an Open follow-up pending Kerry's go-ahead.
- **Answered the `z2w-ai-suite` "Z2W AI Engine" survey** in the coordination bulletin's `global.md`: daily-work-summary is the portfolio's strongest model-drift data point (hand-rolls a four-provider `AI_PROVIDERS` registry in `generate_summary.py`) and a pure-summarization product → it would consume the engine's model-registry + summarization slices over **HTTP service** (Python cron, no Node); hard boundary that the daily email must still send if the engine is down.
- **Next:** all known bulletin feature asks closed; only open item is the optional "bundle the session-metrics hook into the kits" follow-up.

*(Earlier sessions — the v1.9.0 portfolio-stats job and v1.8.0 Skill Vault tally (2026-06-18), the v1.5.2→1.7.0 outage-fix + dead-man's-switch + backfill (2026-06-18), and the v1.0.0 / v1.3.0 / v1.4.0 builds (2026-03-11) — trimmed per the STATUS 3-4-session rule; full history in [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).)*

---
