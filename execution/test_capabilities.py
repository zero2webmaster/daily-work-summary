"""Guard docs/CAPABILITIES.md against falling behind the code.

The capability list is the plain-English record of everything this app does
(Kerry's ruling 2026-11-05, AGENT_PROTOCOL.md "Keep your capability list
current"). A list that silently misses a feature is worse than none, because a
move plan or audit trusts it. This suite fails when:

  * the file is missing or its header is malformed;
  * its "Checked against" version is behind VERSION by a minor version or more;
  * an entry uses a status word outside live / built, off / built, waiting /
    planned (or a retired note);
  * a [code] link points at a file that does not exist;
  * a setting the code reads (env var, Action variable, secret) or a workflow
    name is not mentioned anywhere on the page.

The last check is the one that catches a new feature added without a list
entry: nearly every feature here arrives with a new setting or workflow.

Run:  python3 execution/test_capabilities.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "CAPABILITIES.md"
SCRIPTS = ROOT / ".github" / "scripts"
WORKFLOWS = ROOT / ".github" / "workflows"

# Names the code reads that are GitHub plumbing, not settings anyone sets.
INTERNAL = {"GITHUB_OUTPUT", "GITHUB_EVENT_NAME", "FORCE_RUN"}

ENV_PATTERNS = [
    re.compile(r'environ\.get\(\s*"([A-Z][A-Z0-9_]+)"'),
    re.compile(r'environ\[\s*"([A-Z][A-Z0-9_]+)"\s*\]'),
    re.compile(r'getenv\(\s*"([A-Z][A-Z0-9_]+)"'),
    re.compile(r'_parse_int_env\(\s*"([A-Z][A-Z0-9_]+)"'),
    re.compile(r'\(\s*"([A-Z][A-Z0-9_]+_API_KEY)"'),  # AI provider key table
]
WORKFLOW_SETTING = re.compile(r"\b(?:vars|secrets)\.([A-Z][A-Z0-9_]+)")
WORKFLOW_NAME = re.compile(r"^name:\s*(.+?)\s*$", re.M)
ENTRY = re.compile(r"^- \*\*(.+?)\.\*\* (.+)$", re.M)
CODE_LINK = re.compile(r"\[code\]\(([^)]+)\)")
STATUS = re.compile(
    r"(?:^|\. )(Live|Built, off|Built, waiting|Planned)\b"
    r"|Removed in v\d|Not available"
)

failures: list[str] = []
checks = 0


def check(ok: bool, label: str) -> None:
    global checks
    checks += 1
    print(f"  {'✅' if ok else '❌'} {label}")
    if not ok:
        failures.append(label)


def settings_used() -> set[str]:
    names: set[str] = set()
    for py in SCRIPTS.glob("*.py"):
        text = py.read_text()
        for pat in ENV_PATTERNS:
            names.update(pat.findall(text))
    for yml in WORKFLOWS.glob("*.yml"):
        names.update(WORKFLOW_SETTING.findall(yml.read_text()))
    return names - INTERNAL


def workflow_names() -> set[str]:
    names = set()
    for yml in WORKFLOWS.glob("*.yml"):
        m = WORKFLOW_NAME.search(yml.read_text())
        if m:
            names.add(m.group(1).strip("'\""))
    return names


def minor(v: str) -> tuple[int, int]:
    major, mnr, *_ = (int(x) for x in v.split("."))
    return major, mnr


def main() -> int:
    print("docs/CAPABILITIES.md")
    check(DOC.exists(), "file exists")
    if not DOC.exists():
        return 1
    text = DOC.read_text()
    lines = text.splitlines()

    check(lines[0].strip() == "<!-- capabilities-inventory v1 -->",
          "line 1 is the capabilities-inventory v1 marker")
    m = re.search(r"\*\*Checked against:\*\* v(\d+\.\d+\.\d+) · \d{4}-\d{2}-\d{2}", text)
    check(bool(m), "'Checked against: vX.Y.Z · YYYY-MM-DD' line present")
    version = (ROOT / "VERSION").read_text().strip()
    if m:
        check(minor(m.group(1)) >= minor(version),
              f"checked against v{m.group(1)}, not behind VERSION {version} by a minor")

    entries = ENTRY.findall(text)
    check(len(entries) >= 20, f"at least 20 entries ({len(entries)} found)")
    for name, body in entries:
        check(bool(STATUS.search(body)), f"'{name}' states a status")
        for link in CODE_LINK.findall(body):
            target = (DOC.parent / link).resolve()
            check(target.exists(), f"'{name}' code link exists: {link}")

    print("\nEvery setting the code reads is named on the page")
    used = settings_used()
    check(len(used) >= 15, f"found the settings to compare ({len(used)})")
    for name in sorted(used):
        check(f"`{name}`" in text, f"{name}")

    print("\nEvery workflow is named on the page")
    wf = workflow_names()
    check(len(wf) >= 4, f"found the workflows to compare ({len(wf)})")
    for name in sorted(wf):
        check(f'"{name}"' in text, f'"{name}"')

    print(f"\n{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAILED: {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
