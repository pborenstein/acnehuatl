# Decisions

Architectural decisions for acnehuatl. One heading per decision.

### DEC-001: Read the transcript, not the model (2026-06-16)

**Status**: Accepted

**Context**: A model cannot reliably self-attribute its own identity. It
hallucinates, flattens, or confidently misattributes (cf. the "you is ephemeral"
memorandum, 2026-06-16).

**Decision**: Determine harness/provider/model by reading the harness's JSONL
session log, which records the actual invoked model on every assistant message.
No introspection, no self-report.

**Consequences**: Output is ground truth as long as a session transcript exists
for the cwd. Requires knowing each harness's on-disk layout and message schema.

### DEC-002: Env vars first, filesystem fallback (2026-06-16)

**Status**: Accepted

**Context**: Multiple harnesses may have written session dirs for the same cwd;
filesystem-only detection is ambiguous.

**Decision**: Detect the active harness from inherited env vars first
(`PI_CODING_AGENT*` → pi, `CLAUDE_CODE_*`/`CLAUDE_PROJECT_DIR` → Claude Code).
Fall back to scanning known session roots only when no env signal is present.

**Consequences**: Authoritative when run inside a harness; best-effort (possibly
ambiguous) when run standalone.

### DEC-003: Single file, stdlib only (2026-06-16)

**Status**: Accepted

**Context**: Intended to be called as a thin shim from other tools and skills.

**Decision**: Keep the whole tool in `acnehuatl.py` with no third-party
dependencies, so it runs anywhere Python 3 exists without a venv or install step.

**Consequences**: Trivial to vendor/copy and invoke; no packaging overhead. Trades
off any features that would need external libraries.

### DEC-004: Forgiving cwd → session-dir matching (2026-06-16)

**Status**: Accepted

**Context**: Harnesses encode cwd into a dir name by replacing `/` with `-`, but
the exact on-disk form varies (single vs. doubled dashes, trailing dashes).

**Decision**: Try an exact match first, then a forgiving match that collapses runs
of dashes and ignores trailing-dash differences.

**Consequences**: Survives encoding quirks across harnesses without hardcoding each
variant. Small risk of collision between cwds that differ only by dash runs.

### DEC-005: No cwd argument, always use $PWD (2026-06-17)

**Status**: Accepted

**Context**: The tool's purpose is "who am I?" not "who is running over there?"
A remote cwd can't use env-var detection (the authoritative path), so it falls
back to the ambiguous filesystem scan. Supporting it undermines the tool's
premise.

**Decision**: Remove the optional cwd argument. `identify()` always uses
`os.getcwd()`.

**Consequences**: Simpler interface. The tool only answers the question it can
answer reliably. Querying a remote cwd would require a different tool.
