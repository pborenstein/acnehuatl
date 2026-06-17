---
phase: 0, Foundation
updated: 2026-06-17
last_commit: 2ad4d25
last_entry: 7
---

# Context

## Current Focus

opencode support complete. SQLite reader implemented and verified across three
live model switches (glm-5.2, glm-4.7, deepseek-v4-flash-free). Ready for shim
work or other feature tasks.

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [ ] (idea) Thin shim so skills stamp output with the real incarnation
- [ ] (idea) Tests against captured sample transcripts
- [ ] (idea) Packaging / entry-point so it runs without `python3 acnehuatl.py`

## Blockers

None.

## Context

- Single file, stdlib only, no venv/install needed (DEC-003)
- Reads transcript for ground truth, never asks the model (DEC-001)
- Env-first harness detection, filesystem fallback (DEC-002)
- No cwd argument; always uses $PWD (DEC-005)
- Supports three harnesses: pi (JSONL), Claude Code (JSONL), opencode (SQLite)
- opencode ground truth is `~/.local/share/opencode/opencode.db`, `session.model`
  JSON column; the `~/.claude/` JSONL is fake (DEC-006)
- opencode reader uses read-only, parameterized sqlite3 (`directory = $PWD`)
- Human-readable output strips non-printable characters (`_safe()`)
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Pick one of the idea tasks above. The shim is the stated future direction in the
README: stamp skill output with the real incarnation instead of a generic label.
