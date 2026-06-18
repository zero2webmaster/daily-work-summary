#!/usr/bin/env python3
"""
Session metrics — a Claude Code **Stop hook** prototype.

Reports, at the end of a Claude Code session, how much the admin had to engage:
how many questions they answered through the official answer system
(AskUserQuestion), how many actions the agent took, and how many of those the
admin declined or interrupted.

WHAT IS AND ISN'T MEASURABLE (verified empirically against real transcripts)
----------------------------------------------------------------------------
- **Questions answered — EXACT.** Each `AskUserQuestion` call is a discrete
  `tool_use` block in the transcript; we count the prompts and sum the questions
  inside them.
- **Actions taken — EXACT.** Every tool call is a `tool_use` block.
- **Declined / interrupted — EXACT-ish.** A rejected tool call leaves a
  `tool_result` whose text says the user didn't want to proceed / it was
  rejected. We match those.
- **Plain "allow" approvals — NOT recorded.** When the admin clicks "allow" on a
  permission prompt, Claude Code does NOT write a distinct event to the
  transcript, so a raw "how many times you approved" count is not reconstructable
  from the transcript alone. We therefore report "actions taken" + "declined"
  rather than an approval count, and say so honestly.

USAGE
-----
As a Stop hook, Claude Code pipes a JSON object on stdin that includes
`transcript_path`. Wire it in settings.json (see the module docstring footer):

    {
      "hooks": {
        "Stop": [
          { "hooks": [ { "type": "command",
                         "command": "python3 /ABS/PATH/execution/session_metrics.py" } ] }
        ]
      }
    }

For local testing, pass a transcript path as the first argument instead:

    python3 execution/session_metrics.py ~/.claude/projects/<proj>/<session>.jsonl

Exits 0 always — a metrics report must never block or fail a session.
"""

import json
import sys

# Substrings that identify a tool_result produced by a declined/interrupted call.
# Claude Code phrases rejections a few ways; match defensively + case-insensitively.
DECLINE_MARKERS = (
    "doesn't want to proceed",
    "tool use was rejected",
    "rejected",
    "user has chosen not to",
    "operation was aborted",
    "interrupted by the user",
)


def _iter_lines(path):
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _result_text(block):
    """Flatten a tool_result block's content to lowercase text for matching."""
    content = block.get("content")
    if isinstance(content, str):
        return content.lower()
    try:
        return json.dumps(content).lower()
    except (TypeError, ValueError):
        return ""


def analyze_transcript(path):
    """Return a metrics dict for one session transcript. Pure: file in, dict out."""
    user_turns = 0
    question_prompts = 0
    questions_answered = 0
    actions_taken = 0
    declined = 0
    tools = {}

    for obj in _iter_lines(path):
        msg = obj.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None

        if not isinstance(content, list):
            continue

        # A real user turn = a "user" line containing a `text` block (the typed
        # prompt). Tool results are also "user" lines but carry `tool_result`
        # blocks instead; harness-injected lines are flagged isMeta/isSidechain.
        if (
            obj.get("type") == "user"
            and not obj.get("isMeta")
            and not obj.get("isSidechain")
            and any(isinstance(b, dict) and b.get("type") == "text" for b in content)
        ):
            user_turns += 1

        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")

            if btype == "tool_use":
                name = block.get("name", "?")
                actions_taken += 1
                tools[name] = tools.get(name, 0) + 1
                if name == "AskUserQuestion":
                    question_prompts += 1
                    qs = (block.get("input") or {}).get("questions")
                    questions_answered += len(qs) if isinstance(qs, list) else 1

            elif btype == "tool_result":
                text = _result_text(block)
                if block.get("is_error") and any(m in text for m in DECLINE_MARKERS):
                    declined += 1

    return {
        "user_turns": user_turns,
        "question_prompts": question_prompts,
        "questions_answered": questions_answered,
        "actions_taken": actions_taken,
        "declined_or_interrupted": declined,
        "top_tools": dict(sorted(tools.items(), key=lambda kv: kv[1], reverse=True)),
    }


def format_report(m):
    """One-line-friendly human report. (See limitation note in the module docs.)"""
    top = ", ".join(f"{k}×{v}" for k, v in list(m["top_tools"].items())[:4])
    return (
        "📊 Session metrics — "
        f"you answered {m['questions_answered']} question(s) "
        f"across {m['question_prompts']} prompt(s); "
        f"the agent took {m['actions_taken']} action(s) over {m['user_turns']} of your turns, "
        f"{m['declined_or_interrupted']} declined/interrupted."
        + (f"\n   Top tools: {top}" if top else "")
        + "\n   (Note: plain permission approvals aren't logged in the transcript, "
        "so 'actions taken' + 'declined' is the closest exact measure of approvals.)"
    )


def _resolve_transcript_path():
    # Stop hook: JSON on stdin with transcript_path. Local test: argv[1].
    if len(sys.argv) > 1:
        return sys.argv[1]
    try:
        if not sys.stdin.isatty():
            payload = json.loads(sys.stdin.read() or "{}")
            return payload.get("transcript_path")
    except (json.JSONDecodeError, ValueError):
        return None
    return None


def main():
    path = _resolve_transcript_path()
    if not path:
        print("session_metrics: no transcript_path (pass one as an arg, or run as a Stop hook)")
        sys.exit(0)
    try:
        metrics = analyze_transcript(path)
        print(format_report(metrics))
    except FileNotFoundError:
        print(f"session_metrics: transcript not found: {path}")
    except Exception as e:  # never block a session over a metrics report
        print(f"session_metrics: skipped ({type(e).__name__}: {e})")
    sys.exit(0)


if __name__ == "__main__":
    main()
