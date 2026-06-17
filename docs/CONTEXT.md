---
phase: 0, Foundation
updated: 2026-06-17
last_commit: 2837bb8
last_entry: 6
---

# Context

## Current Focus

Adding opencode support. Harness env detection is done; the remaining work is a
SQLite reader for the real model, since opencode's JSONL is fake (see DEC-006).

## Active Tasks

- [ ] (in progress) opencode support: env detection done, SQLite model reader TODO
- [ ] (idea) Thin shim so skills stamp output with the real incarnation
- [ ] (idea) Tests against captured sample transcripts
- [ ] (idea) Packaging / entry-point so it runs without `python3 acnehuatl.py`

## Blockers

None. The opencode ground-truth location is known (DEC-006); just needs a reader.

## Context

- Single file, stdlib only, no venv/install needed (DEC-003)
- Reads transcript for ground truth, never asks the model (DEC-001)
- Env-first harness detection, filesystem fallback (DEC-002)
- No cwd argument; always uses $PWD (DEC-005)
- opencode sets `OPENCODE=1` (+ `OPENCODE_PID`, `OPENCODE_RUN_ID`)
- CRITICAL: opencode's `~/.claude/projects/*.jsonl` hardcodes `claude-sonnet-4-6`
  and is NOT ground truth. Real model lives in SQLite: `~/.local/share/opencode/
  opencode.db`, `session.model` column as JSON, e.g.
  `{"id":"glm-5.2","providerID":"zai-coding-plan","variant":"default"}` (DEC-006)
- Human-readable output strips non-printable characters (`_safe()`)
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Implement the opencode SQLite reader in `acnehuatl.py`: query `session.model`
(filtered by `directory = $PWD`, latest `time_updated`) and parse the JSON. The
uncommitted `acnehuatl.py` change has env detection but still routes opencode at
the JSONL reader, which returns the wrong model. Replace that branch.
