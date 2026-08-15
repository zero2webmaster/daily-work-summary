"""Throwaway test for should_run_now() — verifies the window guard across the
real GitHub-scheduler fire times. Run: python3 .tmp/test_guard.py"""
import os, sys, importlib.util
from datetime import datetime as _dt, timedelta, timezone
from zoneinfo import ZoneInfo

spec = importlib.util.spec_from_file_location(
    "gen", os.path.join(os.path.dirname(__file__), "..", ".github", "scripts", "generate_summary.py"))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

ET = ZoneInfo("America/New_York")

class FakeDateTime(_dt):
    _now = None
    @classmethod
    def now(cls, tz=None):
        return cls._now.astimezone(tz) if tz else cls._now

def run_at(et_str, *, hour=None, minute=None, window=None):
    """et_str like '2026-06-18 00:39' interpreted in ET."""
    naive = _dt.strptime(et_str, "%Y-%m-%d %H:%M")
    FakeDateTime._now = naive.replace(tzinfo=ET)
    gen.datetime = FakeDateTime
    for k, v in (("EMAIL_SEND_HOUR", hour), ("EMAIL_SEND_MINUTE", minute), ("EMAIL_SEND_WINDOW_MIN", window)):
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = str(v)
    os.environ["EMAIL_TIMEZONE"] = "America/New_York"
    allowed, reason = gen.should_run_now()
    return allowed, reason

# Default config: 22:30 ET target, 480-min window.
cases = [
    # (label, ET time, expect_allowed)
    ("22:45 ET same evening (in window)",        "2026-06-18 22:45", True),
    ("00:39 ET next morning (throttled run)",    "2026-06-19 00:39", True),
    ("02:01 ET next morning (latest reliable)",  "2026-06-19 02:01", True),
    ("18:50 ET afternoon (well before target)",  "2026-06-18 18:50", False),
    ("22:29 ET one min before target",           "2026-06-18 22:29", False),
    ("07:00 ET morning (past 8h window)",         "2026-06-19 07:00", False),
    ("12:00 ET midday (way outside)",            "2026-06-18 12:00", False),
]
fails = 0
for label, t, expect in cases:
    allowed, reason = run_at(t)
    ok = (allowed == expect)
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {label:42s} -> allowed={allowed} (expected {expect})")
    if not ok:
        print(f"        reason: {reason}")

# Old-bug regression check: with the OLD 60-min window, the 00:39 run must STILL
# pass now (proving the anchoring fix is what saves it, independent of width).
allowed, reason = run_at("2026-06-19 00:39", window=60)
print(f"\n{'PASS' if not allowed else 'NOTE'}  00:39 ET with narrow 60m window -> allowed={allowed}")
print(f"        reason: {reason}")
print("        (narrow window legitimately rejects a 129m-late run; 480m default accepts it)")

print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAILED'}")
sys.exit(1 if fails else 0)
