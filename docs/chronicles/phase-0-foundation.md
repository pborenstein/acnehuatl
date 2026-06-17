# Phase 0: Foundation

## Entry 1: Initial implementation (2026-06-16)

**What**: Built `acnehuatl.py`, a single-file CLI that reports which harness and
model are generating the current turn for a given cwd.

**Why**: A model is the least authoritative source on its own identity. For the
TOLTECAYOTL operator role the same amanuensis is incarnated across models (Opus,
glm-5.x, etc.), and provenance — which incarnation said what — matters for
memoranda, zeitgeist, and vault records. The harness transcript is ground truth.

**How**:

- Env-based harness detection (`PI_CODING_AGENT*` → pi, `CLAUDE_CODE_*` → Claude Code)
- Filesystem fallback scanning pi/Claude Code session roots when env is absent
- cwd → session-dir encoding with exact-then-forgiving (collapsed-dash) match
- Per-harness readers: pi walks `model_change` + assistant messages; Claude Code
  takes the last assistant `message.model` (provider assumed anthropic)
- Human-readable and `--json` output; exit codes 0 (found) / 1 (no session) / 2 (no model)

**Decisions**: DEC-001 (transcript not model), DEC-002 (env-first detection),
DEC-003 (single file / stdlib), DEC-004 (forgiving dir matching).

**Files**: `acnehuatl.py`, `README.md` (commit 60bd4b9)

## Entry 2: Project tracking setup (2026-06-17)

**What**: Added `docs/` tracking structure (CONTEXT, IMPLEMENTATION, DECISIONS,
this chronicle) retroactively for the one-commit repo.

**Why**: Establish lightweight ongoing tracking; keep it proportional to a tiny repo.

**Files**: `docs/CONTEXT.md`, `docs/IMPLEMENTATION.md`, `docs/DECISIONS.md`,
`docs/chronicles/phase-0-foundation.md`
