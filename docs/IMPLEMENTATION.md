# Implementation Tracker

Single-file stdlib utility. One phase. See [CONTEXT.md](CONTEXT.md) for hot state,
[DECISIONS.md](DECISIONS.md) for rationale, [chronicles/](chronicles/) for history.

## Phase Overview

| Phase | Name        | Status      | Summary |
|-------|-------------|-------------|---------|
| 0     | Foundation  | In progress | Working CLI that identifies harness + model from session transcripts |

## Phase 0: Foundation

**Goal**: Answer "which model am I, in which harness, right now?" by reading the
harness session transcript (ground truth) rather than asking the model
(unreliable self-attribution).

**Completed**:

- `acnehuatl.py`: single-file CLI, stdlib only
- Env-based harness detection (pi via `PI_CODING_AGENT*`, Claude Code via `CLAUDE_CODE_*`/`CLAUDE_PROJECT_DIR`)
- Filesystem fallback when env signal is absent
- cwd → session-dir name encoding with forgiving (collapsed-dash) match
- Per-harness transcript readers: pi (`model_change` + assistant messages), Claude Code (assistant `message.model`)
- Human-readable and `--json` output; exit codes 0/1/2
- No cwd argument; always uses `os.getcwd()` (DEC-005)
- Control-char stripping in human-readable output (`_safe()`)
- Security review (v4): all actionable findings resolved
- opencode env detection (`OPENCODE=1`) + SQLite model reader (DEC-006)

**In progress**:

- _(none currently)_

**Next / future ideas**:

- Thin shim so skills (memorandum, vault-wrapup) can stamp output with the real
  incarnation instead of the generic "Claude" label
- Tests against captured sample transcripts
- Package/entry-point so it's callable without `python3 acnehuatl.py`

See [chronicles/phase-0-foundation.md](chronicles/phase-0-foundation.md).
