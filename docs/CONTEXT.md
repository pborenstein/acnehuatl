---
phase: 0, Foundation
updated: 2026-06-26
last_commit: 03d8258
last_entry: 11
---

# Context

## Current Focus

Provider is no longer hardcoded for Claude Code: it's read directly where the
transcript has it (pi, opencode, Crush) and derived from the model prefix where
it doesn't (Claude Code only, DEC-009). Provenance is tracked via
`provider_source`. Next is wiring `--label` consumers.

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [x] README rewrite for external audience
- [x] MIT license
- [x] DEC-007: remove filesystem fallback; report unknown when no env signal
- [x] DEC-008: detect Crush (env vars + read_crush on `<cwd>/.crush/crush.db`)
- [x] `--label` primitive (single-source-of-truth `label()`, fail-loud exit codes)
- [x] DEC-009: derive provider for Claude Code (read directly elsewhere)
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
- Provider: read directly for pi/opencode/Crush; DERIVED from model prefix for
  Claude Code (no provider field exists in its transcript). Minimal prefix map
  (`claude`→anthropic, `glm`→z.ai); unknown prefix → `unknown` (DEC-009)
- `provider_source`: `"read"` / `"derived"` / `None`. Human output shows
  `provider:  z.ai (derived)`; `--json` carries the field; `--label` stays clean
- opencode ground truth is `~/.local/share/opencode/opencode.db`, `session.model`
  JSON column; the `~/.claude/` JSONL is fake (DEC-006)
- Crush ground truth is `<cwd>/.crush/crush.db`, `messages.model`/`provider`
  columns; latest assistant message wins (DEC-008)
- Licensed MIT
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Wire a consumer: pick a skill (memorandum or vault-wrapup) and have it call
`acnehuatl.py --label` to stamp output with the real incarnation.
