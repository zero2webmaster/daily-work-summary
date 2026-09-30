# Handoff — Daily Work Summary

**Last session:** 2026-09-30 | **Version:** 1.14.0

## What this project is

A GitHub Actions cron that emails Kerry a daily digest of his commits across all
Z2W repos (target 23:00 ET). 3-layer architecture: directives (SOPs) →
orchestration → deterministic Python in `.github/scripts/`. Delivery: email
(Gmail SMTP) plus optional Airtable/Slack/Discord. An Uptime Kuma Push heartbeat
guards against silent outages. A separate monthly **Portfolio Stats** workflow
writes `stats/portfolio-YYYY-MM.json` into the `z2w-agent-coordination` repo for
https://agents.z2w.us/portfolio.

## Shipped this session (v1.14.0)

- **Portfolio stats now count code as code.** Answered `z2w-agent-command-center`'s
  2026-09-30 question: about 30% of "lines of code" were JSON dumps, lockfiles and
  Drizzle snapshots (one Airtable dump was 116k of contact-registry's 163k lines).
  Lockfiles + `NNNN_snapshot.json` are skipped; JSON/YAML/CSV/XML/SVG go to a new
  `data_lines` field. Takes effect with the 2026-10-01 run.
- **Schema deliberately still `portfolio-stats/v1`.** The command center's parser
  (`src/lib/portfolio-stats.ts`) rejects any other version. The change is
  additive: `loc_method: "code-only"`, `data_lines`, `total_data_lines`.
- Tests: 6/6 suites, `test_portfolio_stats` 48 checks; filter verified against a
  real `cloc` run.

## Outstanding

1. **2026-10-01:** confirm `stats/portfolio-2026-10.json` has `loc_method` and a
   total roughly a third below 2026-09.
   https://github.com/zero2webmaster/daily-work-summary/actions/workflows/portfolio-stats.yml
2. **~2026-10-12:** measure the v1.13.1 send-time change (see STATUS Next Actions #1).
3. Session-metrics hook is OFF at Kerry's request (2026-09-23). Do not re-add it.

## Read first

`STATUS.md` → `ROADMAP.md` → `directives/generate_daily_summary.md` /
`directives/generate_portfolio_stats.md`.

## Starting prompt

> Review the bulletin and proceed with roadmap priorities. Read HANDOFF.md,
> STATUS.md and ROADMAP.md first.
