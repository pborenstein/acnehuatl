---
phase: 0, Foundation
updated: 2026-06-18
last_commit: cbc579f
last_entry: 7
---

# Context

## Current Focus

All three harnesses working. README rewritten for external readers, MIT license
added. Ready for shim work or other feature tasks.

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [x] README rewrite for external audience
- [x] MIT license
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
- Licensed MIT

## Next Session

Pick one of the idea tasks. The shim is the natural next step: let skills stamp
output with the real incarnation instead of a generic label.
