"""Regression test for the cross-repo repetition rollup (v1.13.0).

The complaint: on 2026-08-13 the digest gave three near-identical sections to
one action — `cursor-project-templates: update the capture-learnings block to
v1.2.0` landed in los-osititos, marketing-engine and project-creator, and each
got its own heading, its own AI sentence, and its own bullet. Kerry, 2026-08-14:
"ideally, repetition would be summarized into something like X action took
place on Y repos (repo a, repo b, repo c)".

These checks pin the two properties that keep the rollup honest:
  1. It fires on the real mass-propagation shape.
  2. It NEVER touches a repo that also did its own work, so a section can't
     show a commit count larger than the bullets beneath it.

Run:  python3 execution/test_rollup.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".github" / "scripts"))

os.environ.pop("ROLLUP_MIN_REPOS", None)

import generate_summary as gs  # noqa: E402

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got:  {got}\n          want: {want}")
        failures.append(name)


TEMPLATE_COMMIT = "cursor-project-templates: update the capture-learnings block to v1.2.0"


print("\n1. normalize_subject — what counts as 'the same commit'")

check("identical subjects match",
      gs.normalize_subject(TEMPLATE_COMMIT),
      gs.normalize_subject(TEMPLATE_COMMIT))
check("case and whitespace are ignored",
      gs.normalize_subject("  Update   The Block  "),
      gs.normalize_subject("update the block"))
check("only the subject line matters, not the body",
      gs.normalize_subject("fix the thing\n\nCo-Authored-By: someone"),
      gs.normalize_subject("fix the thing"))
check("different subjects do not collide",
      gs.normalize_subject("update block to v1.2.0")
      == gs.normalize_subject("update block to v1.3.0"),
      False)
check("empty message yields empty key", gs.normalize_subject("   \n  "), "")


print("\n2. find_rollup_groups — Kerry's actual 2026-08-13 case")

aug13 = {
    "los-osititos": [TEMPLATE_COMMIT],
    "marketing-engine": [TEMPLATE_COMMIT],
    "project-creator": [TEMPLATE_COMMIT],
    "ai-studio": ["Add Check Content", "Fix a green pass", "Hand off session #15"],
}
groups = gs.find_rollup_groups(aug13, min_repos=2)
check("one group found", len(groups), 1)
check("group names all three repos", groups[0][1],
      ["los-osititos", "marketing-engine", "project-creator"])
check("group carries the original subject text", groups[0][0], TEMPLATE_COMMIT)
check("the multi-commit repo is untouched",
      "ai-studio" in {r for _, repos in groups for r in repos}, False)


print("\n3. The safety property — a repo that also did its own work is never rolled up")

mixed = {
    "repo-a": [TEMPLATE_COMMIT],
    "repo-b": [TEMPLATE_COMMIT],
    "repo-c": [TEMPLATE_COMMIT, "Ship the actual feature"],
}
groups = gs.find_rollup_groups(mixed, min_repos=2)
check("only the single-commit repos roll up", groups[0][1], ["repo-a", "repo-b"])
check("repo-c keeps its own section",
      "repo-c" in {r for _, repos in groups for r in repos}, False)


print("\n4. Thresholds and opt-outs")

two = {"repo-a": [TEMPLATE_COMMIT], "repo-b": [TEMPLATE_COMMIT]}
check("two repos roll up at the default threshold",
      len(gs.find_rollup_groups(two, min_repos=2)), 1)
check("...but not when the threshold is 3",
      len(gs.find_rollup_groups(two, min_repos=3)), 0)
check("min_repos=0 disables rollup entirely",
      len(gs.find_rollup_groups(aug13, min_repos=0)), 0)
check("a lone repo never rolls up",
      len(gs.find_rollup_groups({"solo": [TEMPLATE_COMMIT]}, min_repos=2)), 0)
check("distinct commits never merge",
      len(gs.find_rollup_groups(
          {"a": ["Update README"], "b": ["Fix the parser"]}, min_repos=2)), 0)
check("collapsed repos are skipped",
      len(gs.find_rollup_groups(
          {"a": [TEMPLATE_COMMIT], "z2w-agent-coordination": [TEMPLATE_COMMIT]},
          min_repos=2, skip={"z2w-agent-coordination"})), 0)
check("empty input is not an error", gs.find_rollup_groups({}, min_repos=2), [])


print("\n5. Group ordering — biggest repetition first")

many = {
    "a1": ["shared one"], "a2": ["shared one"], "a3": ["shared one"],
    "b1": ["shared two"], "b2": ["shared two"],
}
groups = gs.find_rollup_groups(many, min_repos=2)
check("two groups", len(groups), 2)
check("the 3-repo group sorts first", groups[0][1], ["a1", "a2", "a3"])
check("the 2-repo group sorts second", groups[1][1], ["b1", "b2"])


print("\n6. get_rollup_min_repos — the ROLLUP_MIN_REPOS Action variable")


def with_env(value):
    if value is None:
        os.environ.pop("ROLLUP_MIN_REPOS", None)
    else:
        os.environ["ROLLUP_MIN_REPOS"] = value
    return gs.get_rollup_min_repos()


check("unset uses the default", with_env(None), gs.DEFAULT_ROLLUP_MIN_REPOS)
check("blank uses the default", with_env("   "), gs.DEFAULT_ROLLUP_MIN_REPOS)
check("explicit number is honored", with_env("4"), 4)
check("'none' disables", with_env("none"), 0)
check("'off' disables", with_env("off"), 0)
check("0 disables", with_env("0"), 0)
check("1 is meaningless and disables", with_env("1"), 0)
check("garbage falls back to the default",
      with_env("banana"), gs.DEFAULT_ROLLUP_MIN_REPOS)
with_env(None)


print("\n====================================================")
if failures:
    print(f"{len(failures)} check(s) FAILED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("All checks passed.")
