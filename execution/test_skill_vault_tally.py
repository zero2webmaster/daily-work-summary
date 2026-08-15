#!/usr/bin/env python3
"""Offline unit test for format_skill_vault_tally().

Runs the pure formatter against representative skill-vault-stats/v1 payloads —
no GitHub, no network. Mirrors the .tmp/test_guard.py pattern from v1.5.2.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0] / ".." / ".github" / "scripts"))
from generate_summary import format_skill_vault_tally  # noqa: E402

FULL = {
    "schema": "skill-vault-stats/v1",
    "as_of": "2026-06-18",
    "by_day": {
        "2026-06-16": {"created": 6, "improved": 9},
        "2026-06-18": {"created": 3, "improved": 5},
    },
    "totals": {"skills": 28, "created": 28, "improved": 31},
}

cases = [
    # (label, stats, today, expected)
    (
        "today present, both counts",
        FULL, "2026-06-18",
        "🧠 **Skill Vault:** 3 created, 5 improved today · 28 skills total",
    ),
    (
        "today present, improved only",
        {"as_of": "2026-06-18", "by_day": {"2026-06-18": {"created": 0, "improved": 4}},
         "totals": {"skills": 30}},
        "2026-06-18",
        "🧠 **Skill Vault:** 4 improved today · 30 skills total",
    ),
    (
        "today present, created only",
        {"as_of": "2026-06-18", "by_day": {"2026-06-18": {"created": 2, "improved": 0}},
         "totals": {"skills": 30}},
        "2026-06-18",
        "🧠 **Skill Vault:** 2 created today · 30 skills total",
    ),
    (
        "stale artifact (no entry for today) — note as-of, show total only",
        FULL, "2026-06-19",
        "🧠 **Skill Vault:** 28 skills total *(Vault stats as of 2026-06-18)*",
    ),
    (
        "as_of == today but no skill activity today — total only, no stale note",
        {"as_of": "2026-06-18", "by_day": {"2026-06-16": {"created": 6, "improved": 9}},
         "totals": {"skills": 28}},
        "2026-06-18",
        "🧠 **Skill Vault:** 28 skills total",
    ),
    (
        "today entry has both zero — treated as no activity",
        {"as_of": "2026-06-18", "by_day": {"2026-06-18": {"created": 0, "improved": 0}},
         "totals": {"skills": 28}},
        "2026-06-18",
        "🧠 **Skill Vault:** 28 skills total",
    ),
    ("empty dict -> None", {}, "2026-06-18", None),
    ("not a dict -> None", "nope", "2026-06-18", None),
    ("no totals, no today -> None", {"as_of": "2026-06-18", "by_day": {}}, "2026-06-18", None),
]

failures = 0
for label, stats, today, expected in cases:
    got = format_skill_vault_tally(stats, today)
    ok = got == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failures += 1
        print(f"        expected: {expected!r}")
        print(f"        got:      {got!r}")

print(f"\n{len(cases) - failures}/{len(cases)} passed")
sys.exit(1 if failures else 0)
