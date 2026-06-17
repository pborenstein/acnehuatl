---
phase: 0, Foundation
updated: 2026-06-17
last_commit: 9c60c4e
last_entry: 3
---

# Context

## Current Focus

Working single-file CLI (`acnehuatl.py`) that identifies harness + model from
session transcripts. Docs cleaned up to match style conventions.

## Active Tasks

- [ ] (idea) Thin shim so skills stamp output with the real incarnation
- [ ] (idea) Tests against captured sample transcripts
- [ ] (idea) Packaging / entry-point so it runs without `python3 acnehuatl.py`

## Blockers

None.

## Context

- Single file, stdlib only, no venv/install needed (DEC-003)
- Reads transcript for ground truth, never asks the model (DEC-001)
- Env-first harness detection, filesystem fallback (DEC-002)
- Supports two harnesses: pi and Claude Code
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Pick one of the idea tasks above. The shim is the stated future direction in the
README. Read this file first, then IMPLEMENTATION.md Phase 0 if more detail needed.
