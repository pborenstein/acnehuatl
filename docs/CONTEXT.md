---
phase: 0, Foundation
updated: 2026-06-17
last_commit: d2e00ff
last_entry: 5
---

# Context

## Current Focus

Working single-file CLI. Security review completed (v4, all actionable findings
resolved). Ready for shim work or other feature tasks.

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
- No cwd argument; always uses $PWD (DEC-005)
- Human-readable output strips non-printable characters (`_safe()`)
- Security review in `docs/reviews/2026-06-17-security-review.md` (v4)
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Pick one of the idea tasks above. The shim is the stated future direction in the
README. Read this file first, then IMPLEMENTATION.md Phase 0 if more detail needed.
