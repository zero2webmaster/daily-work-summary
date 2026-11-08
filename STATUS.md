# Daily Work Summary - Project Status

**Last Updated:** 2026-11-08 (v2.1.0)

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

### Decision: Retire Airtable rather than move it to Neon
**Date:** 2026-10-31 (v2.0.0)
**Rationale:** Kerry wanted off Airtable (API limits) and suggested Neon. Nothing read the Airtable copy; the dashboard reads `summaries/` on GitHub, which already holds every day. Migrating would have built a database nobody uses. Old `DELIVERY_METHOD` values are tolerated so a stale variable can never silence the email.

### Decision: Raw `requests` for Airtable client (not `pyairtable`) — superseded by v2.0.0
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

### Decision: Don't build the approved outside timer while GitHub delivers on time
**Date:** 2026-10-31 (v1.15.1)
**Rationale:** Kerry approved a Cloudflare Worker trigger on 2026-10-15 to fix late delivery. From Oct 17 the email arrived 23:16–23:31 ET every night (14 nights), so the problem it was approved for no longer exists. A new token and a second platform are a standing cost; it stays designed in ROADMAP and is re-opened if delivery drifts past ~00:30 ET again. The extra slot crons are now load-bearing and are guarded by `test_workflow.py`.

### Decision: Comma-separated DELIVERY_METHOD for Slack/Discord
**Date:** 2026-03-11
**Rationale:** Allows any combination of channels without combinatorial explosion of named values (e.g. `email,slack,discord`). The `both` alias is preserved for backward compat. Unknown values are warned-and-dropped rather than erroring, so adding new methods in future is non-breaking.

---

## ✅ Next Actions

0. **Confirm v2.1.0 (Nov 9):** the Nov 8 email should include cloud-session commits (commerce-engine had many that day). Run time grows slightly (one extra API query per repo).

1. **Confirm v1.15.1 (after 2026-11-01).** No "Commit summary to repo" failure in the nightly runs; the second run near 23:15 ET should log "already exists … skipping". Note: DST ends Nov 1, so the slot shifts to the 04:xx UTC cron entries — check the Nov 1 and Nov 2 send times too.
2. ✅ **Airtable fully retired (2026-10-31):** `AIRTABLE_*` secrets and variables deleted from the repo; Kerry deleted the Airtable token and renamed the base "Daily Work Summary - DEPRECATED" (nothing reads it).
3. **Session-metrics hook: ON HOLD.** Kerry turned the global Stop hook off on 2026-09-23 and asked that it not be re-added without asking him.
4. **Kerry's call — realign the misdated June archive** (2026-06-18 → 06-30, 13 files). He chose July-only on 2026-07-31; re-open only if he asks.
5. Test Slack delivery: add `SLACK_WEBHOOK_URL` secret, set `DELIVERY_METHOD=slack`
6. Test Discord delivery: add `DISCORD_WEBHOOK_URL` secret, set `DELIVERY_METHOD=discord`

---

## 🔧 Tech Debt

- Version drift existed (VERSION=1.2.6, README=1.2.3) — fixed in v1.3.0

---

## 📊 Recent Updates

### Session: 2026-11-08 - Phone (cloud-session) commits now counted (v2.1.0)

- **`commerce-engine`'s bulletin Q answered.** Kerry's phone work on Nov 7 was missing from the email: cloud sessions commit as `Claude <noreply@anthropic.com>`, which the `author=<login>` filter dropped (27 commits that day, via GitHub search). Each repo is now also queried for that identity and merged by sha; `EXTRA_COMMIT_AUTHORS` overrides, `none` reverts.
- **Kerry chose (phone, multiple choice):** merge to `main` and backfill Nov 7, archive only.
- **Verified:** 10/10 suites, new `test_cloud_commits.py` 17/17; CI green on the PR. **Canary:** Nov 7 backfill went 17 commits/10 repos → 57/11 (commerce-engine 2 → 29, command center 0 → 6), no bot commits.

### Session: 2026-10-31 (cont.) - Airtable retired (v2.0.0)

- Kerry said yes: `DELIVERY_METHOD` set to `email`; Airtable client, setup script and workflow, delivery code and env vars removed. Backfill now uses `DELIVERY_METHOD=none`. Leftover `airtable`/`both` values still send the email (`test_delivery.py`, 10 checks). 9/9 suites.
- Deleted this session's two temporary git worktrees at Kerry's request (both clean and pushed first).

### Session: 2026-10-31 - Nightly push failure fixed; outside timer shelved (v1.15.1)

- **Nightly "CI failed: Commit summary to repo" (Oct 28–31) fixed.** Not two runs racing, as first thought: the concurrency group did serialize them. The second run checked out the commit it was *queued* on, so it never saw the first run's pushed summary, rebuilt it, and lost the push. Checkout now uses the branch tip. The email was never doubled.
- **Approved outside timer not built.** Delivery has been 23:16–23:31 ET every night since Oct 17. Re-open criteria in ROADMAP.
- **Checked, not bugs:** Oct 20–21 had no summary because Kerry's own account made no commits (only bots and phone dispatches, which the digest doesn't count).
- **Verified:** 8/8 suites; new `test_workflow.py` 7/7 and fails against the old workflow; all 5 workflow YAMLs parse.

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

*(Earlier sessions — the v1.13.1 send-time + bulletin triage (2026-09-28), the v1.13.0 digest-density + tracked-tests build (2026-08-15), the v1.11.0 date fix (2026-07-31), the v1.10.0 messages-sent metric (2026-06-19), the v1.9.0 portfolio-stats job and v1.8.0 Skill Vault tally (2026-06-18), the v1.5.2→1.7.0 outage-fix + dead-man's-switch + backfill (2026-06-18), and the v1.0.0 / v1.3.0 / v1.4.0 builds (2026-03-11) — trimmed per the STATUS 3-4-session rule; full history in [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).)*

---
