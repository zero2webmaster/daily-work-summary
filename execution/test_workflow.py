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

Run:  python3 execution/test_workflow.py
"""

import sys
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / ".github/workflows/daily-summary.yml"

failures: list[str] = []


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
    check("23:xx ET slot cron is present", "10,25,40 3,4 * * *" in crons)
    check("hourly fallback cron is present", "5 * * * *" in crons)
    check("manual trigger is available", "workflow_dispatch" in triggers)

    print(f"\n{7 - len(failures)}/7 checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
