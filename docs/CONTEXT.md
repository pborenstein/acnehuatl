---
phase: 0, Foundation
updated: 2026-06-21
last_commit: fe49d65
last_entry: 10
---

# Context

## Current Focus

`--label` mode landed: the shim primitive that emits one capturable
`provider/model (harness)` line and fails loudly. Next is wiring consumers.
(Built on DEC-008: Crush is now a detected harness; all four harnesses working.)

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [x] README rewrite for external audience
- [x] MIT license
- [x] DEC-007: remove filesystem fallback; report unknown when no env signal
- [x] DEC-008: detect Crush (env vars + read_crush on `<cwd>/.crush/crush.db`)
- [x] `--label` primitive (single-source-of-truth `label()`, fail-loud exit codes)
- [ ] Wire skill consumers (memorandum, vault-wrapup) to call `--label`
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
- `--label`: on failure prints nothing, exits 1 (no session) / 2 (no model);
  callers must treat that as fatal, never guess. `label()` is the only place
  the incarnation string is built.
- Licensed MIT
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Wire a consumer: pick a skill (memorandum or vault-wrapup) and have it call
`acnehuatl.py --label` to stamp output with the real incarnation.
