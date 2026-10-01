---
phase: 0, Foundation
updated: 2026-10-01
last_commit: 166e925
last_entry: 12
---

# Context

## Current Focus

Five harnesses supported: ZCode (desktop app) detection landed via the
`ZCODE_*` env family and a `model_usage` join in `~/.zcode/cli/db/db.sqlite`
(DEC-010). The first `--label` consumer is live: the ekranoplan.org colophon
stamps its model provenance from `--label` output. Next is wiring the skill
consumers.

## Active Tasks

- [x] opencode support: env detection + SQLite model reader (DEC-006)
- [x] README rewrite for external audience
- [x] MIT license
- [x] DEC-007: remove filesystem fallback; report unknown when no env signal
- [x] DEC-008: detect Crush (env vars + read_crush on `<cwd>/.crush/crush.db`)
- [x] `--label` primitive (single-source-of-truth `label()`, fail-loud exit codes)
- [x] DEC-009: derive provider for Claude Code (read directly elsewhere)
- [x] DEC-010: detect ZCode (env family + read_zcode on the desktop DB)
- [x] First `--label` consumer: ekranoplan.org colophon provenance stamp
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
- Supports five harnesses: pi, Claude Code (JSONL), opencode, Crush, ZCode (SQLite)
- Provider: read directly for pi/opencode/Crush/ZCode; DERIVED from model prefix for
  Claude Code (no provider field exists in its transcript). Minimal prefix map
  (`claude`→anthropic, `glm`→z.ai); unknown prefix → `unknown` (DEC-009)
- `provider_source`: `"read"` / `"derived"` / `None`. Human output shows
  `provider:  z.ai (derived)`; `--json` carries the field; `--label` stays clean
- opencode ground truth is `~/.local/share/opencode/opencode.db`, `session.model`
  JSON column; the `~/.claude/` JSONL is fake (DEC-006)
- Crush ground truth is `<cwd>/.crush/crush.db`, `messages.model`/`provider`
  columns; latest assistant message wins (DEC-008)
- ZCode ground truth is `~/.zcode/cli/db/db.sqlite`: `model_usage` joined to
  `session` on `directory`; latest completed `main_turn` row wins; provider
  strings carry an `account:` prefix and are reported verbatim (DEC-010)
- Licensed MIT
- Docs style: no em dashes, arrows (→) are fine, colons for list separators

## Next Session

Wire a skill consumer: pick a skill (memorandum or vault-wrapup) and have it call
`acnehuatl.py --label` to stamp output with the real incarnation, following the
pattern proven by the ekranoplan.org colophon stamp.
