# Handoff — Daily Work Summary

**Last session:** 2026-11-25 | **Version:** 2.2.0

## What this project is

A GitHub Actions cron that emails Kerry a daily digest of his commits across all
Z2W repos (target 23:00 ET). 3-layer architecture: directives (SOPs) →
orchestration → deterministic Python in `.github/scripts/`. Delivery: email
(Gmail SMTP) plus optional Slack/Discord. An Uptime Kuma Push heartbeat
guards against silent outages. A separate monthly **Portfolio Stats** workflow
writes `stats/portfolio-YYYY-MM.json` into the `z2w-agent-coordination` repo for
https://agents.z2w.us/portfolio.

## Shipped 2026-11-25 (v2.2.0, cloud session from Kerry's phone)

- **Scheduled starts cut from ~30 a day to 3** (answers `audit-engine`'s 2026-11-24 Q; ~900 → ~90–150 billed Actions minutes/month). Crons: `10,25 3 * 4-10 *`, `10,25 4 * 12,1,2 *`, `10,25 3,4 * 3,11 *`, `40 5 * * *`. Tuned to 23:00 ET; change them if `EMAIL_SEND_HOUR` moves.
- `test_workflow.py` now walks a year of nights through the crons (11 checks). Merged to `main` at Kerry's yes.
- **Watch:** send time stays ~23:15 ET and the Actions tab shows ~3 runs/day. A missed night trips the Uptime Kuma heartbeat; the fallback plan is the Worker timer in ROADMAP.

## Shipped 2026-11-16 (v2.1.1, cloud session from Kerry's phone)

- `docs/CAPABILITIES.md`: plain-English list of all 28 features with status and code link (closes `audit-engine`'s 2026-11-13 ACTION). **Update it in the same commit as any feature change.**
- `execution/test_capabilities.py` (89 checks) fails when a setting or workflow the code uses is missing from the list. 11/11 suites.
- Confirmed v2.1.0 in production: Nov 8 email counted 90 commits / 19 repos; summaries every night through Nov 15.

## Shipped 2026-10-31 (v1.15.1 → v2.0.0)

- **v2.0.0: Airtable delivery removed** (Kerry's yes, 2026-10-31). `DELIVERY_METHOD=email` set live; backfill uses the new `none` mode; leftover `airtable`/`both` values still send the email. 9/9 suites.

- **Fixed the nightly "CI failed: Commit summary to repo" alert (Oct 28–31).**
  Two runs land ~1 min apart near 23:15 ET. The concurrency group serialized
  them, but the second checked out the commit it was queued on (`github.sha`),
  not `main`'s tip, so it missed the first run's summary file, rebuilt it, and
  its push was rejected. Checkout now uses `ref: ${{ github.ref }}`.
- New `execution/test_workflow.py` (7 checks) guards the checkout ref, the
  concurrency group and the slot crons. `PyYAML` added to `requirements.txt`.
  8/8 suites.
- **Did NOT build the approved Cloudflare Worker timer.** Since Oct 17 the email
  arrives 23:16–23:31 ET every night. Re-open criteria are in ROADMAP.

## Outstanding

1. **After 2026-11-01:** confirm no push failures, and check send times across
   the DST change (EST from Nov 1 uses the 04:xx UTC cron entries).
2. Done: `AIRTABLE_*` secrets/variables deleted; Kerry deleted the token and renamed the base to "… - DEPRECATED".
3. Session-metrics hook is OFF at Kerry's request (2026-09-23). Do not re-add it.

## Read first

`STATUS.md` → `ROADMAP.md` → `directives/generate_daily_summary.md` /
`directives/generate_portfolio_stats.md`.

## Starting prompt

> Review the bulletin and proceed with roadmap priorities. Read HANDOFF.md,
> STATUS.md and ROADMAP.md first.
