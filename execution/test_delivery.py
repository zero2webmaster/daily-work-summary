"""Checks for parse_delivery_methods() after Airtable was removed (v2.0.0).

The point of these checks: a leftover DELIVERY_METHOD value from before the
removal (`email,airtable`, `both`, `airtable`) must still deliver the email,
never silence it, and `none` (used by the backfill workflow) must deliver
nothing so a backfill can't send a burst of emails.

Run:  python3 execution/test_delivery.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".github/scripts"))
from generate_summary import parse_delivery_methods  # noqa: E402

CASES = [
    (None, {"email"}, "unset defaults to email"),
    ("", {"email"}, "empty defaults to email"),
    ("email", {"email"}, "email"),
    ("email,airtable", {"email"}, "Kerry's pre-v2 value keeps the email"),
    ("both", {"email"}, "legacy 'both' alias now means email"),
    ("airtable", {"email"}, "airtable alone falls back to email, never silence"),
    ("none", set(), "none = archive only (backfill)"),
    ("NONE", set(), "none is case-insensitive"),
    ("slack,discord", {"slack", "discord"}, "webhooks only"),
    ("email, slack ,bogus", {"email", "slack"}, "unknown value dropped"),
]


def main() -> int:
    failures = 0
    for raw, expected, name in CASES:
        got = parse_delivery_methods(raw)
        ok = got == expected
        failures += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {raw!r} -> {sorted(got)}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
