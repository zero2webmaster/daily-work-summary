"""Run every tracked test suite in this repo and report a single verdict.

Each suite is a standalone script that prints its own checks and exits non-zero
on failure (see `execution/test_*.py`). This runner exists so CI and a local
developer share ONE command, and so a suite that is present but unrunnable is
reported as a FAILURE rather than quietly contributing nothing.

Why it counts what it found: an empty run must never look like a pass. If the
glob matches no suites, this exits non-zero — "I examined nothing" and "I
examined everything and found nothing wrong" are different results.

Run:  python3 execution/run_tests.py
"""

import subprocess
import sys
from pathlib import Path

EXECUTION_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXECUTION_DIR.parent


def main() -> int:
    suites = sorted(EXECUTION_DIR.glob("test_*.py"))

    if not suites:
        print("FAIL: no test suites matched execution/test_*.py")
        print("      An empty run is not a pass — check the suite location.")
        return 1

    print(f"Running {len(suites)} test suite(s) from {EXECUTION_DIR}\n")

    failed: list[str] = []
    for suite in suites:
        rel = suite.relative_to(REPO_ROOT)
        print(f"{'=' * 60}\n{rel}\n{'=' * 60}")
        result = subprocess.run(
            [sys.executable, str(suite)],
            cwd=REPO_ROOT,
        )
        if result.returncode == 0:
            print(f"\n  ✅ {rel}\n")
        else:
            print(f"\n  ❌ {rel} (exit {result.returncode})\n")
            failed.append(str(rel))

    print("=" * 60)
    passed = len(suites) - len(failed)
    print(f"{passed}/{len(suites)} suite(s) passed")
    if failed:
        for name in failed:
            print(f"  FAILED: {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
