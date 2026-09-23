# Coordination Onboarding — daily-work-summary

> 📦 **Delivered 2026-09-22 by `z2w-starter-kit` v0.37.0** to a repo scaffolded before this
> file joined the Z2W project standard. It is a pointer and needs no editing.

> **Read this first if you're a fresh agent on `daily-work-summary`.** This is a short
> pointer, not the full guide. `daily-work-summary` participates in the Z2W cross-project
> coordination bulletin, and the canonical, always-current onboarding primer lives
> in the bulletin repo — **not here** — so there is a single source of truth.

## Where the canonical primer lives

Read **`COORDINATION_ONBOARDING.md`** at the root of the coordination bulletin repo
(`zero2webmaster/z2w-agent-coordination`). There is ONE local clone, at
`~/.cache/z2w-coordination` — the Desktop path
`~/Desktop/Zero2Webmaster/AI/Cursor Projects/z2w-agent-coordination/` is a symlink to it.

🔴 **Never `git pull` or edit in that shared clone.** Take a private workspace
first — from the clone, `WS="$(bash scripts/agent-workspace.sh daily-work-summary)"` then
`cd "$WS"` — and read and write only there. The `## Agent Coordination` section of
this project's `CLAUDE.md` has the exact steps; where it and the primer disagree,
the live `AGENT_PROTOCOL.md` wins.

The primer orients you to the three core Z2W systems (the coordination bulletin,
the Skill Vault, and the starter-kit + Templates) and walks you through joining
the bulletin as `daily-work-summary`.

## The one rule that must not drift

The `## Agent Coordination` section of this project's `CLAUDE.md` / `AGENTS.md` is
either a short **pointer** to the live `AGENT_PROTOCOL.md` (preferred) or a
**verbatim** copy of it carrying the current
`<!-- z2w-agent-coordination canonical-block vX.Y.Z -->` fingerprint. **Never
paraphrase it**, and never copy a version-frozen block from another project or
from a primer snapshot — that is exactly how canonical-block drift happens.

## Your bulletin file

This project's bulletin file is `projects/daily-work-summary.md`. Read it in protocol order at
session start (`## Incidents` → `## Inbox from Kerry` → `## Open questions` →
`## Heads-ups`), then `global.md`. Rewrite `## Current focus` at session end.

---

*Pointer emitted at scaffold time by `@zero2webmaster/starter-kit` (mirrors
[[instantiate-z2w-project]]). The canonical primer it links is owned by
`z2w-agent-coordination` — improve it THERE, never fork a per-project copy.*
