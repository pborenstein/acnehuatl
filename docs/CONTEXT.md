---
phase: 0, Foundation
updated: 2026-06-18
last_commit: cbc579f
last_entry: 8
---

# Context

## Current Focus

DEC-007 shipped: removed the unsound filesystem fallback so the tool never
reports a harness/model it can't verify. Next up is Crush detection (the
harness that exposed the bug).

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [x] README rewrite for external audience
- [x] MIT license
- [x] DEC-007: remove filesystem fallback; report unknown when no env signal
- [ ] Detect Crush as a harness (needs: Crush env vars, readable session store)
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
- Supports three harnesses: pi (JSONL), Claude Code (JSONL), opencode (SQLite)
- opencode ground truth is `~/.local/share/opencode/opencode.db`, `session.model`
  JSON column; the `~/.claude/` JSONL is fake (DEC-006)
- Licensed MIT

## Next Session

Add Crush as a detected harness: find what env var(s) Crush exports and where
it stores session transcripts, then add an env branch in `_detect_from_env()`
and a reader. This is what exposed DEC-007.
