# Daily Work Summary - Project Status

**Last Updated:** 2026-10-12 (v1.15.0)

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

### Decision: Data files are not code in portfolio stats, and the schema stays v1
**Date:** 2026-09-30 (v1.14.0)
**Rationale:** About 30% of the portfolio's "lines of code" were JSON dumps, lockfiles and Drizzle snapshots, so the biggest-repo ranking was measuring data, not work. Lockfiles and snapshots are generated and now skipped entirely; other data formats move to a separate `data_lines` field so nothing is hidden. The schema string was deliberately **not** bumped: the command center's parser returns nothing for any schema but `portfolio-stats/v1`, so a bump would have blanked `/portfolio` on the next monthly run. The change is additive, and `loc_method: "code-only"` marks which months use it. Corollary: **only bump the schema after the reader accepts the new version.**

### Decision: Comma-separated DELIVERY_METHOD for Slack/Discord
**Date:** 2026-03-11
**Rationale:** Allows any combination of channels without combinatorial explosion of named values (e.g. `email,slack,discord`). The `both` alias is preserved for backward compat. Unknown values are warned-and-dropped rather than erroring, so adding new methods in future is non-breaking.

---

## ✅ Next Actions

1. **Kerry's call — external send trigger.** v1.13.1's extra cron slots made delivery *later*: median 01:50 ET (Aug 25–Sep 28) → 03:29 ET (Sep 29–Oct 11), range 01:35–05:39. Proposed fix in ROADMAP ("Send Time: External Trigger"); filed as `[→ Kerry]` on the bulletin. Don't build until he answers.
2. **Check the first v1.15.0 email (covers 2026-10-12, arrives early 10-13).** Most bullets should start with a version; no theme line should ask a question. `summaries/daily-summary-2026-10-12.md`.
3. **Session-metrics hook: ON HOLD.** Kerry turned the global Stop hook off on 2026-09-23 and asked that it not be re-added without asking him.
4. **Kerry's call — realign the misdated June archive** (2026-06-18 → 06-30, 13 files). He chose July-only on 2026-07-31; re-open only if he asks.
5. Test Slack delivery: add `SLACK_WEBHOOK_URL` secret, set `DELIVERY_METHOD=slack`
6. Test Discord delivery: add `DISCORD_WEBHOOK_URL` secret, set `DELIVERY_METHOD=discord`

---

## 🔧 Tech Debt

- Version drift existed (VERSION=1.2.6, README=1.2.3) — fixed in v1.3.0

---

## 📊 Recent Updates

### Session: 2026-10-12 - Bullet versions + no-questions theme line (v1.15.0)

- **Kerry's two unread inbox items (Oct 8, Oct 9) done.** The theme line had asked him for "the complete commit messages" three nights running. Cause: the AI was fed 80-char subjects ending in `...`. It now reads whole subjects, and any reply that asks something becomes "More info needed for a summary".
- **Version first on every bullet** where one exists: subject → `Version:` trailer → the repo's `VERSION` file at that commit. Redundant `repo-name:` prefixes dropped. Truncation 80 → 85.
- **Send-time experiment measured: it failed.** Median 01:50 → 03:29 ET. Filed `[→ Kerry]` proposing an external trigger.
- **Oct 1 portfolio stats confirmed:** `loc_method: "code-only"`; total code 2,169,168 → 1,550,714 (−29%); 290,569 data lines; contact-registry 163k → 37k code + 123k data.
- **Verified:** 7/7 suites (`test_bullets` 35 new checks, built on the real Oct 7–9 replies); `VERSION` lookup checked live on two repos.

### Session: 2026-09-30 - Portfolio stats count code as code (v1.14.0)

- **Answered `z2w-agent-command-center`'s 2026-09-30 question** (Kerry had asked why `contact-registry` showed the most code). 116k of its 163k "lines" were one Airtable JSON dump; about 30% of the portfolio total was data and lockfiles.
- **Changed the counting:** lockfiles and Drizzle `NNNN_snapshot.json` are skipped; JSON/YAML/CSV/XML/SVG move from `loc` to a new `data_lines` field. Takes effect with the 2026-10-01 run.
- **Kept schema `portfolio-stats/v1`** after reading the command center's parser, which rejects any other version. Added `loc_method: "code-only"` and `total_data_lines` instead.
- **Verified:** 6/6 suites, `test_portfolio_stats` 21 → 48 checks; one real `cloc` run on a scratch fixture confirmed the filter and the split.
- **Bulletin:** shared clone had another session's uncommitted edits, so this session read and wrote through a separate worktree instead of pulling over them.

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

*(Earlier sessions — the v1.11.0 date fix (2026-07-31), the v1.10.0 messages-sent metric (2026-06-19), the v1.9.0 portfolio-stats job and v1.8.0 Skill Vault tally (2026-06-18), the v1.5.2→1.7.0 outage-fix + dead-man's-switch + backfill (2026-06-18), and the v1.0.0 / v1.3.0 / v1.4.0 builds (2026-03-11) — trimmed per the STATUS 3-4-session rule; full history in [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).)*

---
