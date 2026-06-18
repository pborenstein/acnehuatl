---
phase: 0, Foundation
updated: 2026-06-18
last_commit: d10f8bc
last_entry: 9
---

# Context

## Current Focus

DEC-008 shipped: Crush is now a detected harness (env var + per-project
SQLite reader). All four harnesses working. Verified live mid-session.

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [x] README rewrite for external audience
- [x] MIT license
- [x] DEC-007: remove filesystem fallback; report unknown when no env signal
- [x] DEC-008: detect Crush (env vars + read_crush on `<cwd>/.crush/crush.db`)
- [ ] (idea) Thin shim so skills stamp output with the real incarnation
- [ ] (idea) Tests against captured sample transcripts
- [ ] (idea) Packaging / entry-point so it runs without `python3 acnehuatl.py`

## Blockers

None.

## Context

- Single file, stdlib only, no venv/install needed (DEC-003)
- Reads transcript for ground truth, never asks the model (DEC-001)
- Env-only harness detection; no filesystem fallback (DEC-002, superseded by DEC-007)
- No cwd argument; always uses $PWD (DEC-005)
- Supports four harnesses: pi, Claude Code (JSONL), opencode, Crush (SQLite)
- opencode ground truth is `~/.local/share/opencode/opencode.db`, `session.model`
  JSON column; the `~/.claude/` JSONL is fake (DEC-006)
- Crush ground truth is `<cwd>/.crush/crush.db`, `messages.model`/`provider`
  columns; latest assistant message wins (DEC-008)
- Both SQLite readers use read-only, parameterized queries
- Human-readable output strips non-printable characters (`_safe()`)
- Licensed MIT
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Pick an idea task. The shim is the stated future direction in the README:
stamp skill output with the real incarnation instead of a generic label.
