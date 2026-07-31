"""Clock-frozen regression test for the summary date label (v1.11.0).

The bug: the nightly run fires after midnight (GitHub's throttled scheduler
delivers a 23:00 ET slot around 00:30 the next morning), fetched the previous
day's commits, and then labeled them with the wall-clock date at run time — so
Kerry's Jul 31 00:31 email said "Fri Jul 31" over Thursday's work.

Run:  python3 execution/test_summary_date.py
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".github" / "scripts"))

os.environ["EMAIL_TIMEZONE"] = "America/New_York"
os.environ["EMAIL_SEND_HOUR"] = "23"
os.environ["EMAIL_SEND_MINUTE"] = "00"
os.environ.pop("BACKFILL_DATE", None)

import generate_summary as gs  # noqa: E402

ET = ZoneInfo("America/New_York")
failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got:  {got}\n          want: {want}")
        failures.append(name)


class _Frozen(datetime):
    """datetime subclass whose .now() returns a fixed instant."""

    _at = None

    @classmethod
    def now(cls, tz=None):
        return cls._at.astimezone(tz) if tz else cls._at.replace(tzinfo=None)


def freeze(at: datetime):
    _Frozen._at = at
    return mock.patch.object(gs, "datetime", _Frozen)


print("\n1. _target_local — which send slot is this run delivering?")
# The real failing run: fired 00:31 ET Jul 31, delivering the 23:00 Jul 30 slot.
check(
    "00:31 Jul 31 delivers the Jul 30 slot",
    gs._target_local(datetime(2026, 7, 31, 0, 31, tzinfo=ET)).date().isoformat(),
    "2026-07-30",
)
check(
    "23:10 Jul 30 (rare same-evening run) delivers the Jul 30 slot",
    gs._target_local(datetime(2026, 7, 30, 23, 10, tzinfo=ET)).date().isoformat(),
    "2026-07-30",
)
check(
    "exactly 23:00 Jul 30 delivers the Jul 30 slot",
    gs._target_local(datetime(2026, 7, 30, 23, 0, tzinfo=ET)).date().isoformat(),
    "2026-07-30",
)
check(
    "22:59 Jul 30 (one minute early) still delivers Jul 29",
    gs._target_local(datetime(2026, 7, 30, 22, 59, tzinfo=ET)).date().isoformat(),
    "2026-07-29",
)
check(
    "04:31 Jul 31 (the later throttled run) also delivers Jul 30",
    gs._target_local(datetime(2026, 7, 31, 4, 31, tzinfo=ET)).date().isoformat(),
    "2026-07-30",
)

print("\n2. _resolve_window — label and window must name the SAME day")
with freeze(datetime(2026, 7, 31, 0, 31, tzinfo=ET)):
    since, until, label = gs._resolve_window()
check("label is the reported day, not the run day", label, "2026-07-30")
check(
    "window starts at Jul 30 00:00 ET",
    since.astimezone(ET).isoformat(),
    "2026-07-30T00:00:00-04:00",
)
check(
    "window ends at Jul 30 23:59:59 ET (closed calendar day)",
    until.astimezone(ET).isoformat(),
    "2026-07-30T23:59:59-04:00",
)

print("\n3. Pre-midnight run must not claim commits that haven't happened")
with freeze(datetime(2026, 7, 30, 23, 10, tzinfo=ET)):
    since, until, label = gs._resolve_window()
check("label is Jul 30", label, "2026-07-30")
check(
    "window is clamped to now, not the future end-of-day",
    until.astimezone(ET).isoformat(),
    "2026-07-30T23:10:00-04:00",
)

print("\n4. Backfill semantics unchanged (and now identical to nightly)")
os.environ["BACKFILL_DATE"] = "2026-06-10"
with freeze(datetime(2026, 7, 31, 9, 0, tzinfo=ET)):
    since, until, label = gs._resolve_window()
os.environ.pop("BACKFILL_DATE")
check("backfill label is the requested day", label, "2026-06-10")
check(
    "backfill window is the whole closed day",
    (since.astimezone(ET).isoformat(), until.astimezone(ET).isoformat()),
    ("2026-06-10T00:00:00-04:00", "2026-06-10T23:59:59-04:00"),
)

print("\n5. should_run_now still fires for the real throttled run times")
for at, want_allowed in [
    (datetime(2026, 7, 31, 0, 31, tzinfo=ET), True),    # +91m  — the real send
    (datetime(2026, 7, 31, 4, 31, tzinfo=ET), True),    # +331m — still in window
    (datetime(2026, 7, 30, 20, 11, tzinfo=ET), False),  # +1271m — outside
    (datetime(2026, 7, 31, 12, 0, tzinfo=ET), False),   # +780m  — outside
]:
    with freeze(at):
        allowed, reason = gs.should_run_now()
    check(f"{at:%b %d %H:%M} allowed={want_allowed}", allowed, want_allowed)

print("\n6. The guard's target and the label agree (the actual bug)")
for at in [
    datetime(2026, 7, 31, 0, 31, tzinfo=ET),
    datetime(2026, 7, 31, 4, 31, tzinfo=ET),
    datetime(2026, 7, 30, 23, 10, tzinfo=ET),
    datetime(2026, 1, 1, 0, 5, tzinfo=ET),  # year boundary
]:
    with freeze(at):
        guard_day = gs._target_local().date().isoformat()
        _, _, label = gs._resolve_window()
    check(f"{at:%Y-%m-%d %H:%M} guard=={label}", guard_day, label)

print("\n7. Provenance stamp gates idempotency (transition safety)")
check(
    "stamp names the covered day",
    gs.summary_stamp("2026-07-30"),
    '<!-- daily-summary/v2 covers="2026-07-30" -->',
)
check(
    "a legacy (unstamped) file does NOT look already-sent",
    gs.summary_stamp("2026-07-31") in "<div>Daily Work Summary — Fri Jul 31, 2026</div>",
    False,
)
check(
    "a correctly-stamped file DOES look already-sent",
    gs.summary_stamp("2026-07-31") in gs.summary_stamp("2026-07-31") + "<div>...</div>",
    True,
)
check(
    "a stamp for a different day does not satisfy this slot",
    gs.summary_stamp("2026-07-31") in gs.summary_stamp("2026-07-30") + "<div>...</div>",
    False,
)

print("\n" + "=" * 52)
if failures:
    print(f"{len(failures)} FAILED: {', '.join(failures)}")
    sys.exit(1)
print("All checks passed.")
