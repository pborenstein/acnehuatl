---
phase: 0 — Foundation
updated: 2026-06-17
last_commit: 60bd4b9
last_entry: 2
---

# Context

## Current Focus

Working single-file CLI (`acnehuatl.py`) that identifies harness + model from
session transcripts. Project tracking just established.

## Active Tasks

- [ ] (idea) Thin shim so skills stamp output with the real incarnation
- [ ] (idea) Tests against captured sample transcripts
- [ ] (idea) Packaging / entry-point so it runs without `python3 acnehuatl.py`

## Blockers

None.

## Context

- Single file, stdlib only — no venv/install needed (DEC-003)
- Reads transcript for ground truth, never asks the model (DEC-001)
- Env-first harness detection, filesystem fallback (DEC-002)
- Supports two harnesses: pi and Claude Code

## Next Session

Pick one of the idea tasks above. The shim is the stated future direction in the
README. Read this file first, then IMPLEMENTATION.md Phase 0 if more detail needed.
