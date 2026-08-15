#!/usr/bin/env python3
"""Regression test for session_metrics.py — focus on the messages-sent metric
(Kerry's 2026-06-18 19:03 ask) plus the existing counts. Builds a synthetic
transcript and asserts analyze + format behavior. Run: python3 .tmp/test_session_metrics.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "execution"))
import session_metrics as sm  # noqa: E402


def _line(obj):
    return json.dumps(obj)


def _write(lines):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(_line(o) for o in lines))
    return path


def make_transcript():
    """3 real admin chats, 1 AskUserQuestion (2 questions), 1 declined tool, plus
    meta/tool-result noise that must NOT be counted as messages sent."""
    return [
        # real typed admin message #1
        {"type": "user", "message": {"content": [{"type": "text", "text": "do X"}]}},
        # assistant takes an action
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {}}]}},
        # tool_result is a "user" line but must NOT count as a message sent
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "content": "ok"}]}},
        # harness-injected meta line — must NOT count
        {"type": "user", "isMeta": True, "message": {"content": [
            {"type": "text", "text": "<system-reminder>noise</system-reminder>"}]}},
        # real typed admin message #2
        {"type": "user", "message": {"content": [{"type": "text", "text": "do Y"}]}},
        # AskUserQuestion with 2 questions
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "AskUserQuestion",
             "input": {"questions": [{"q": 1}, {"q": 2}]}}]}},
        # a declined tool call
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True,
             "content": "The user doesn't want to proceed with this tool use."}]}},
        # real typed admin message #3
        {"type": "user", "message": {"content": [{"type": "text", "text": "thanks"}]}},
    ]


def run():
    path = _write(make_transcript())
    try:
        m = sm.analyze_transcript(path)
    finally:
        os.unlink(path)

    checks = {
        "user_turns == 3 (3 real chats, not tool-results/meta)": m["user_turns"] == 3,
        "questions_answered == 2": m["questions_answered"] == 2,
        "question_prompts == 1": m["question_prompts"] == 1,
        "actions_taken == 3 (Bash+AskUserQuestion+Edit)": m["actions_taken"] == 3,
        "declined_or_interrupted == 1": m["declined_or_interrupted"] == 1,
    }
    report = sm.format_report(m)
    checks["report leads with messages sent"] = "you sent 3 message(s) to the agent" in report

    failed = [k for k, ok in checks.items() if not ok]
    for k, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {k}")
    print(f"\nReport:\n{report}\n")
    if failed:
        print(f"{len(failed)} FAILED")
        sys.exit(1)
    print(f"All {len(checks)} checks passed.")


if __name__ == "__main__":
    run()
