"""Structural checks on .github/workflows/daily-summary.yml.

The nightly job relies on three workflow-level properties that no Python test
of generate_summary.py can see. Each one, if dropped, has already caused (or
would cause) a real failure:

1. The checkout step must check out the branch tip (`ref: ${{ github.ref }}`),
   not the commit the run was queued on. Without it, a run that waited in the
   concurrency queue misses the summary the previous run just pushed,
   regenerates it, and fails on push. (Nightly incidents, 2026-10-28..31.)
2. A concurrency group must serialize runs, or two runs can both pass the
   idempotency check before either commits.
3. The 23:xx ET slot crons must stay. Since 2026-10-17 they are what delivers
   the email at 23:16-23:31 ET; the hourly cron alone landed it 01:35-05:39.
4. The schedule must stay small (v2.2.0). Every scheduled start is billed as
   at least one Actions minute, even when the guard skips it; the old hourly
   line made ~30 starts a day (~900 billed minutes/month, a third of the
   account's allowance). Checked by walking every day of a year through the
   cron lines in America/New_York, so a daylight-saving gap fails here, not
   as a missing email in March or November.

Run:  python3 execution/test_workflow.py
"""

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / ".github/workflows/daily-summary.yml"

ET = ZoneInfo("America/New_York")
SEND_HOUR = 23            # Kerry's live EMAIL_SEND_HOUR
WINDOW_MIN = 480          # DEFAULT_SEND_WINDOW_MIN in generate_summary.py
MAX_STARTS_PER_DAY = 5    # 3 on most days, 5 in March/November

failures: list[str] = []


def _field(spec: str, value: int) -> bool:
    """Match one cron field. Supports '*', numbers, ',' lists and 'a-b' ranges,
    which is all this workflow uses; anything else fails loudly."""
    if spec == "*":
        return True
    for part in spec.split(","):
        if "-" in part:
            lo, hi = part.split("-")
            if int(lo) <= value <= int(hi):
                return True
        elif int(part) == value:
            return True
    return False


def starts_on(cron: str, day: date) -> list[datetime]:
    """UTC start times a 5-field cron line produces on one UTC calendar day."""
    minute, hour, dom, month, dow = cron.split()
    if not (_field(dom, day.day) and _field(month, day.month)
            and _field(dow, (day.weekday() + 1) % 7)):
        return []
    return [datetime(day.year, day.month, day.day, h, m, tzinfo=timezone.utc)
            for h in range(24) if _field(hour, h)
            for m in range(60) if _field(minute, m)]


def year_walk(crons: list[str]) -> dict:
    """For each send night of 2027 (a whole DST cycle, incl. both changeovers),
    list the ET times of scheduled starts that fall in that night's window."""
    first, last = date(2027, 1, 1), date(2027, 12, 31)
    nights: dict[date, list[datetime]] = {}
    busiest = 0
    d = first
    while d <= last:
        utc_starts = [t for c in crons for t in starts_on(c, d)]
        busiest = max(busiest, len(utc_starts))
        for t in utc_starts:
            local = t.astimezone(ET)
            # Most recent past 23:00 ET, as _target_local() anchors it.
            target = local.replace(hour=SEND_HOUR, minute=0, second=0, microsecond=0)
            if local < target:
                target -= timedelta(days=1)
            if (local - target) <= timedelta(minutes=WINDOW_MIN):
                nights.setdefault(target.date(), []).append(local)
        d += timedelta(days=1)
    return {"nights": nights, "busiest": busiest}


def check(name: str, ok: bool) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)


def main() -> int:
    wf = yaml.safe_load(WORKFLOW.read_text())
    # PyYAML parses the bare key `on` as boolean True.
    triggers = wf.get("on", wf.get(True, {}))
    steps = wf["jobs"]["generate-and-send"]["steps"]

    checkout = [s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")]
    check("exactly one checkout step", len(checkout) == 1)
    ref = (checkout[0].get("with") or {}).get("ref") if checkout else None
    check("checkout uses the branch tip (ref: ${{ github.ref }})", ref == "${{ github.ref }}")

    conc = wf.get("concurrency") or {}
    check("concurrency group is set", bool(conc.get("group")))
    check("concurrency does not cancel the in-progress run", conc.get("cancel-in-progress") is False)

    crons = [c.get("cron") for c in triggers.get("schedule", [])]
    check("manual trigger is available", "workflow_dispatch" in triggers)
    check("no hourly cron (each start bills a minute)", "5 * * * *" not in crons
          and not any(c.split()[1] == "*" for c in crons))

    walk = year_walk(crons)
    nights = walk["nights"]
    covered = [date(2027, 1, 1) + timedelta(days=i) for i in range(364)]
    missing = [n for n in covered if n not in nights]
    check("every night of 2027 has a start in the send window", not missing)
    if missing:
        print(f"        missing nights: {missing[:5]}")
    no_slot = [n for n in covered
               if not any(t.date() == n and t.hour == SEND_HOUR and t.minute <= 15
                          for t in nights.get(n, []))]
    check("every night has a start at 23:00-23:15 ET (DST-safe)", not no_slot)
    if no_slot:
        print(f"        no 23:xx slot on: {no_slot[:5]}")
    thin = [n for n in covered if len(nights.get(n, [])) < 3]
    check("every night has at least 3 chances to send", not thin)
    if thin:
        print(f"        fewer than 3 on: {thin[:5]}")
    check(f"at most {MAX_STARTS_PER_DAY} scheduled starts on any day "
          f"(busiest: {walk['busiest']})", walk["busiest"] <= MAX_STARTS_PER_DAY)
    starts_2027 = sum(len(starts_on(c, date(2027, 1, 1) + timedelta(days=i)))
                      for c in crons for i in range(365))
    check(f"under 1,500 scheduled starts a year (got {starts_2027}; "
          f"the hourly schedule was ~10,950)", starts_2027 < 1500)

    total = 11
    print(f"\n{total - len(failures)}/{total} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
