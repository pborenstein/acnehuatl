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

**Status**: Partially superseded by DEC-007 (filesystem fallback removed)

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

### DEC-006: opencode ground truth is SQLite, not the JSONL (2026-06-17)

**Status**: Accepted

**Context**: opencode stores session files in `~/.claude/projects/` using the
Claude Code JSONL format, which led to the assumption the existing Claude Code
reader would work. It does not. opencode writes a hardcoded
`message.model = "claude-sonnet-4-6"` into that JSONL for compatibility, while
the actual invoked model is something else entirely (e.g. glm-5.2). Reading the
JSONL returns the wrong model. DEC-001's premise (the transcript is ground truth)
is violated by opencode's JSONL.

**Decision**: For opencode sessions, read the real model from opencode's own
SQLite database at `~/.local/share/opencode/opencode.db`. The `session` table has
a `model` column holding JSON: `{"id":"...","providerID":"...","variant":"..."}`.
Filter by `directory = os.getcwd()`, take the latest `time_updated`. The
`providerID` is the provider (e.g. `zai-coding-plan`); `id` is the model
(e.g. `glm-5.2`).

**Consequences**: opencode needs its own reader (a SQLite query), not the JSONL
walker. stdlib `sqlite3` is available, so DEC-003 (no third-party deps) holds.
The harness is still detected from env (`OPENCODE=1`). The `~/.claude/` JSONL
must not be trusted for opencode sessions.

### DEC-007: No filesystem fallback for harness detection (2026-06-18)

**Status**: Accepted

**Context**: DEC-002 fell back to scanning known session roots when no harness
env var was set. That fallback guessed the harness from which session dirs
exist for the cwd, which is unsound: a leftover session dir from a *previous*
run of a different harness gets reported as the current one. Observed in the
wild — acnehuatl run inside Crush (which sets none of `PI_CODING_AGENT*`,
`CLAUDE_CODE_*`, `OPENCODE*`) reported `harness: pi` by finding a stale pi
session dir for the same cwd, then read a model from that old transcript.
Nothing about that output was true of the current process. acnehuatl's whole
premise is reliable self-identification; a plausible-but-wrong guess is worse
than an honest "unknown".

**Decision**: Harness detection is env-var-only. When no harness env var is
present, `detect_harness_session_dir` returns `(None, None)`; `identify`
reports the cwd with harness/provider/model as unknown (exit code 1). The
filesystem is still used *within* a known harness to locate that harness's
session dir, but never to decide *which* harness is running.

**Consequences**: Running outside any supported harness now honestly reports
"unknown" instead of a wrong guess. acnehuatl can no longer identify a
harness that does not export an env var; future harness support must be added
as an env-var branch in `_detect_from_env`. The cwd is always reported, so
callers still know where the lookup was attempted.

### DEC-008: Crush detection via per-project SQLite DB (2026-06-18)

**Status**: Accepted

**Context**: Crush is a fourth harness that exports `CRUSH=1` (and
`AGENT=crush` / `AI_AGENT=crush`). It was the harness that exposed DEC-007:
run inside Crush, the deleted filesystem fallback misreported it as pi.
Crush stores ground truth in a per-project SQLite DB at `<cwd>/.crush/crush.db`,
not a JSONL. Its `messages` table has `model` and `provider` columns per
assistant message, and mid-session model switches are recorded as separate
rows (observed `glm-4.7` and `glm-5.1` in one session).

**Decision**: Detect Crush from `CRUSH`/`AGENT`/`AI_AGENT` env vars in
`_detect_from_env`. Add `read_crush(cwd)` which opens
`<cwd>/.crush/crush.db` read-only, takes the latest session by
`updated_at`, then the most recent assistant message with a non-empty `model`.
The current model = that latest assistant message's `model`/`provider`
(last-one-wins, like Claude Code).

**Consequences**: Crush is now a first-class detected harness. The per-project
DB location means the cwd must be readable and the DB must exist; if absent,
the harness is detected (via env) but model/provider are reported unknown
(honest, exit 1), consistent with opencode when its DB is missing. stdlib
`sqlite3` is reused, so DEC-003 (no third-party deps) holds.

### DEC-009: Derive provider for Claude Code, read directly elsewhere (2026-06-26)

**Status**: Accepted

**Context**: `read_claude_code()` hardcoded `("anthropic", model)`. That
assumption is wrong: Claude Code can be driven by a non-Anthropic model via a
proxy (a live session ran Claude Code on `glm-5.2`, a Z.ai model). Scanning
every assistant-message key and top-level entry key in a real transcript
confirmed Claude Code carries NO provider field of any kind, the only
provider-shaped signal is `message.model` itself. The other three readers DO
have ground truth: pi (`message.provider`), opencode (`session.model.providerID`),
Crush (`messages.provider`). Provider is a pure function of the model name for
all stock hosted models (no two providers ship identically-named models).

**Decision**: Read provider directly where the transcript has it (pi, opencode,
Crush). For Claude Code, where no field exists, DERIVE it from the model prefix
via a minimal map (`claude`→anthropic, `glm`→z.ai) plus `_infer_provider()`.
Unknown prefix → `None` → `unknown` (consistent with DEC-007's "report unknown
when no signal"). Track provenance with a `provider_source` field: `"read"`,
`"derived"`, or `None`. Human-readable output annotates derived values
(`provider:  z.ai (derived)`); `--label` stays a clean incarnation string
(provenance only in `--json`).

**Alternatives**: (a) Drop provider entirely, rely on model name alone. Rejected:
the read sources carry real routing/billing signal the model name lacks (e.g.
opencode's `zai-coding-plan`), so the column earns its keep where it's real.
(b) A broad prefix map covering every known lab. Rejected: aspirational guessing;
only map prefixes we've actually observed, grow as real cases appear.

**Consequences**: The original `anthropic` hardcode is gone. For Claude Code the
provider is now correct (`z.ai` for `glm-*`) but explicitly labeled as derived,
never masquerading as ground truth. `--label` output for this session changed
from `anthropic/glm-5.2 (claude-code)` to `z.ai/glm-5.2 (claude-code)`.
Unrecognized model prefixes under Claude Code now yield `unknown/<model>`
rather than a wrong `anthropic`.
