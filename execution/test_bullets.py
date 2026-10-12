"""Regression test for bullet versions and the AI fallback line (v1.15.0).

Two complaints from Kerry:
  2026-10-08: the theme line read "I don't have enough information to summarize
  the theme ... Could you please share the complete commit messages?" — "If a
  summary can't be created it should just say: More info needed for a summary."
  Same day: "Some projects give version number at beginning of each bullet ...
  ideally they all would", and bullets about five characters longer.

The AI replies below are copied from the real Oct 7-9 archive.

Run:  python3 execution/test_bullets.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".github" / "scripts"))

import generate_summary as gs  # noqa: E402

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got:  {got!r}\n          want: {want!r}")
        failures.append(name)


print("AI fallback line")
FALLBACK = gs.AI_NO_SUMMARY_TEXT

check(
    "Oct 7 reply -> fallback",
    gs.clean_ai_summary(
        "I don't have enough information to summarize the theme across commits, "
        "as only one partial commit message has been provided. Could you please "
        "share the complete commit messages or additional commits you'd like me to analyze?"
    ),
    FALLBACK,
)
check(
    "Oct 8 multi-line reply -> fallback",
    gs.clean_ai_summary(
        "I don't have access to the full commit messages needed to identify the "
        'development theme. The text provided appears to be truncated (ending with "three old ...").\n\n'
        "Could you provide the complete commit messages? That will allow me to "
        "accurately summarize the work in a single professional sentence"
    ),
    FALLBACK,
)
check("sentinel -> fallback", gs.clean_ai_summary("NOT_ENOUGH_INFO"), FALLBACK)
check("sentinel with period -> fallback", gs.clean_ai_summary("NOT_ENOUGH_INFO."), FALLBACK)
check(
    "normal summary kept, trailing period dropped",
    gs.clean_ai_summary("Registration tables gained sorting and search."),
    "Registration tables gained sorting and search",
)
check(
    "summary quoting a question is NOT a request",
    gs.clean_ai_summary("Post-event reports now ask 'Did it take place?' and count volunteers."),
    "Post-event reports now ask 'Did it take place?' and count volunteers",
)
check(
    "multi-line summary flattened to one line",
    gs.clean_ai_summary("Letters gained a P.S.\nand a two-line sign-off."),
    "Letters gained a P.S. and a two-line sign-off",
)
check("empty -> None", gs.clean_ai_summary("   "), None)
check("None -> None", gs.clean_ai_summary(None), None)

print("\nTruncation length")
check("limit is 85", gs.MAX_MSG_LENGTH, 85)
long_subject = "x" * 120
check("85-char cut", len(gs.truncate(long_subject)), 85)
check("AI sees whole subject up to 200", gs.truncate("y" * 150, gs.AI_SUBJECT_LENGTH), "y" * 150)

print("\nBullet versions")
calls: list[str] = []


def lookup(v):
    def _f():
        calls.append(v)
        return v
    return _f


check(
    "leading version kept as-is",
    gs.bullet_text("v0.3.0 - Shows and episodes", "podcast-engine", lookup("9.9.9")),
    "v0.3.0 - Shows and episodes",
)
check("no lookup when subject has a version", calls, [])
check(
    "redundant repo prefix dropped, version now first",
    gs.bullet_text("event-engine: v0.118.0 — drag to reorder columns", "event-engine"),
    "v0.118.0 — drag to reorder columns",
)
check(
    "version mid-subject: not duplicated",
    gs.bullet_text("STATUS — v0.111.1 live (c1ee3a0)", "event-engine", lookup("0.111.1")),
    "STATUS — v0.111.1 live (c1ee3a0)",
)
check(
    "Version: trailer used before any API lookup",
    gs.bullet_text(
        "Portfolio stats count code as code\n\nDetails.\n\nVersion: 1.14.0\n",
        "daily-work-summary",
        lookup("0.0.1"),
    ),
    "v1.14.0 - Portfolio stats count code as code",
)
calls.clear()
check(
    "VERSION file lookup fills the gap",
    gs.bullet_text("Add daily summary for 2026-10-11", "daily-work-summary", lookup("1.14.0")),
    "v1.14.0 - Add daily summary for 2026-10-11",
)
check("lookup called once", calls, ["1.14.0"])
check(
    "no VERSION file -> bullet unchanged",
    gs.bullet_text("docs: crypto history started", "financial-records", lambda: None),
    "docs: crypto history started",
)


def boom():
    raise RuntimeError("API down")


check(
    "lookup error never drops the bullet",
    gs.bullet_text("Handoff notes", "audit-engine", boom),
    "Handoff notes",
)
added = gs.bullet_text("z" * 120, "r", lambda: "1.2.3")
check("added version sits outside the 85-char budget", added, "v1.2.3 - " + "z" * 82 + "...")

print("\nVERSION file reader")


class FakeExc(gs.GithubException):
    def __init__(self, status):
        super().__init__(status, {}, {})


class FakeRepo:
    def __init__(self, full_name, contents):
        self.full_name = full_name
        self.contents = contents
        self.calls = 0

    def get_contents(self, path, ref):
        self.calls += 1
        if self.contents is None:
            raise FakeExc(404)

        class C:
            decoded_content = self.contents.encode()
        return C()


reader = gs.VersionFileReader()
with_file = FakeRepo("o/with", "1.4.2\n")
check("reads VERSION", reader.read(with_file, "a1"), "1.4.2")
reader.read(with_file, "a1")
check("cached per commit", with_file.calls, 1)
without = FakeRepo("o/without", None)
reader.read(without, "b1")
reader.read(without, "b2")
check("404 remembered per repo", without.calls, 1)
check("non-version content ignored", gs.VersionFileReader().read(FakeRepo("o/x", "Project: 1.0"), "c"), None)
check("leading v accepted", gs.VersionFileReader().read(FakeRepo("o/y", "v2.0.1"), "c"), "2.0.1")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {failures}")
    sys.exit(1)
print("All bullet/fallback checks passed.")
