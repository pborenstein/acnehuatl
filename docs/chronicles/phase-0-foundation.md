# Phase 0: Foundation

## Entry 1: Initial implementation (2026-06-16)

**What**: Built `acnehuatl.py`, a single-file CLI that reports which harness and
model are generating the current turn for a given cwd.

**Why**: A model is the least authoritative source on its own identity. For the
TOLTECAYOTL operator role the same amanuensis is incarnated across models (Opus,
glm-5.x, etc.), and provenance (which incarnation said what) matters for
memoranda, zeitgeist, and vault records. The harness transcript is ground truth.

**How**:

- Env-based harness detection (`PI_CODING_AGENT*` → pi, `CLAUDE_CODE_*` → Claude Code)
- Filesystem fallback scanning pi/Claude Code session roots when env is absent
- cwd → session-dir encoding with exact-then-forgiving (collapsed-dash) match
- Per-harness readers: pi walks `model_change` and assistant messages; Claude Code
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

## Entry 3: Doc style cleanup (2026-06-17)

**What**: Removed em dashes from all docs, replaced with colons or commas.
Kept arrows (→) as intentional style for mapping notation.

**Why**: Align docs with style guide (gist `80b6e1a9`). Em dashes are banned;
arrows and colons are the preferred separators.

**Files**: `README.md`, `docs/CONTEXT.md`, `docs/DECISIONS.md`,
`docs/IMPLEMENTATION.md`, `docs/chronicles/phase-0-foundation.md`

## Entry 4: Remove cwd argument (2026-06-17)

**What**: Removed the optional cwd argument from `identify()` and the CLI.
The tool now always uses `os.getcwd()`.

**Why**: "Who am I?" is the only question the tool can answer reliably. A remote
cwd bypasses env-var detection and falls back to ambiguous filesystem scanning.
"Who is running over there?" is a different tool.

**Decisions**: DEC-005 (no cwd argument, always $PWD).

**Files**: `acnehuatl.py`, `README.md`

## Entry 5: Security review and Finding 2 fix (2026-06-17)

**What**: Security review conducted by glm-5.2 (pi), went through v1-v3.
Finding 1 (cwd arg path-steering) was already resolved by Entry 4. Fixed
Finding 2: added `_safe()` to strip non-printable characters from
transcript-sourced strings in human-readable output. Review updated to v4.

**Why**: Human-readable output printed raw model/provider strings from the
transcript. A tampered transcript with terminal control sequences would be
emitted to the terminal.

**Files**: `acnehuatl.py`, `docs/reviews/2026-06-17-security-review.md`

## Entry 6: opencode investigation (2026-06-17)

**What**: Investigated why acnehuatl reports the wrong model under opencode
(reported `claude-sonnet-4-6`, actual was `glm-5.2`). Cracked the case: the
`~/.claude/projects/*.jsonl` files opencode writes hardcode `claude-sonnet-4-6`
for compatibility and are not ground truth. The real model lives in opencode's
SQLite DB (`~/.local/share/opencode/opencode.db`), `session.model` column, as
JSON `{"id":"glm-5.2","providerID":"zai-coding-plan","variant":"default"}`.

**Why**: opencode is a target harness. The tool is useless there if it returns a
hardcoded Anthropic model name. The whole premise (transcript = ground truth)
broke for opencode and had to be re-grounded.

**How**:

- Added opencode env detection (`OPENCODE=1`, `OPENCODE_PID`, `OPENCODE_RUN_ID`)
- Confirmed via `sqlite3` that `session.model` holds the real provider + model
- Uncommitted `acnehuatl.py` change: env detection works, but the opencode branch
  still routes at the JSONL reader and returns the wrong model. SQLite reader is
  the remaining work.

**Decisions**: DEC-006 (opencode ground truth is SQLite, not the JSONL).

**Files**: `acnehuatl.py` (uncommitted), `docs/CONTEXT.md`, `docs/DECISIONS.md`

## Entry 7: opencode SQLite reader (2026-06-17)

**What**: Implemented `read_opencode()` in `acnehuatl.py`, completing opencode
support. Routes opencode sessions to a read-only SQLite query against
`~/.local/share/opencode/opencode.db` instead of the fake JSONL. `identify()`
now branches: opencode queries the DB by cwd; pi/Claude Code keep the JSONL flow.

**Why**: Entry 6 left the reader unwired. The JSONL branch returned a hardcoded
`claude-sonnet-4-6`, so opencode was unusable until the real source was read.

**How**:

- `read_opencode(cwd)`: opens the DB read-only (`mode=ro`, URI), runs a
  parameterized `SELECT model, id FROM session WHERE directory = ? ORDER BY
  time_updated DESC LIMIT 1`, parses the `model` JSON (`providerID`, `id`)
- `identify()` calls `read_opencode()` and returns `(provider, model, session_id)`
  before reaching the JSONL path
- `detect_harness_session_dir()` returns `("opencode", None)`; opencode has no
  session dir, only the DB

**Verified**: live-tested across three incarnations switched mid-session:
`glm-5.2` (zai-coding-plan), `glm-4.7`, `deepseek-v4-flash-free` (opencode). All
reported correctly.

**Decisions**: DEC-006.

**Files**: `acnehuatl.py`, `docs/CONTEXT.md`, `docs/IMPLEMENTATION.md`

## Entry 8: Remove filesystem fallback for harness detection (2026-06-18)

**What**: Removed the filesystem-guessing fallback in
`detect_harness_session_dir`. When no harness env var is set, the function now
returns `(None, None)` and the tool reports unknown (cwd only) instead of
guessing a harness from leftover session dirs.

**Why**: Running acnehuatl inside Crush (which exports none of
`PI_CODING_AGENT*`, `CLAUDE_CODE_*`, `OPENCODE*`) reported `harness: pi` by
finding a stale pi session dir for the same cwd, then read a model from that
old transcript. Nothing about that output described the current process. The
tool's premise is reliable self-identification; a plausible-but-wrong guess is
worse than an honest unknown.

**How**:

- Deleted the no-env fallback block that scanned pi/Claude Code session roots
- Filesystem matching still used *within* a known harness to locate that
  harness's own session dir, never to decide *which* harness is running
- Updated README, CONTEXT, DECISIONS; added DEC-007, marked DEC-002 partially
  superseded

**Verified**: pi/claude-code/opencode env branches unchanged and correct;
clean env now reports unknown with exit 1.

**Decisions**: DEC-007 (no filesystem fallback).

**Files**: `acnehuatl.py`, `README.md`, `docs/CONTEXT.md`, `docs/DECISIONS.md`,
`docs/IMPLEMENTATION.md`

## Entry 9: Crush harness support (2026-06-18)

**What**: Added Crush as a fourth detected harness. Env detection via
`CRUSH`/`AGENT=crush`/`AI_AGENT=crush`; reads the model from Crush's
per-project SQLite DB at `<cwd>/.crush/crush.db`.

**Why**: Crush was the harness that exposed DEC-007 (its sessions were
misreported as pi by the deleted filesystem fallback). Having removed that
fallback, the honest fix is to teach acnehuatl about Crush directly so it
reports correctly instead of unknown.

**How**:

- `_detect_from_env()`: added Crush branch (checks `CRUSH`, `AGENT=crush`,
  `AI_AGENT=crush`)
- `detect_harness_session_dir()`: returns `("crush", None)` (no session dir;
  the DB is per-project)
- `read_crush(cwd)`: opens `<cwd>/.crush/crush.db` read-only (`mode=ro`,
  URI), takes the latest session by `updated_at`, then the most recent
  assistant message with a non-empty `model`. Current model = that message's
  `model`/`provider` (last-one-wins, like Claude Code)
- `identify()`: wired the crush branch alongside opencode

**Verified**: live mid-session model switches observed in the same Crush
session (`glm-4.7`, `glm-5.1`, `claude-haiku-4-5`); all reported correctly.
pi/claude-code/opencode/unknown paths unchanged.

**Decisions**: DEC-008 (Crush detection via per-project SQLite DB).

**Files**: `acnehuatl.py`, `README.md`, `docs/CONTEXT.md`, `docs/DECISIONS.md`,
`docs/IMPLEMENTATION.md`

## Entry 10: --label mode (2026-06-21)

**What**: Added a `--label` flag that prints only the canonical incarnation
string `provider/model (harness)` on one line.

**Why**: The shim idea (let skills stamp output with the real incarnation)
needs a primitive that emits exactly one machine-capturable line and fails
loudly rather than guessing. `--json`/human output were both too noisy.

**How**:

- `label(result)`: single source of truth, returns the string or `None` if no model
- `--label` in `main()`: on success prints the line, exit 0; on failure prints
  nothing and exits 1 (no session file) or 2 (session but no model), so
  `LABEL=$(acnehuatl.py --label)` yields an empty string + failing exit, never a guess

**Verified**: all three exit paths exercised via stubbed `identify()` — found
(0, label), no session (1, empty), session-no-model (2, empty).

**Files**: `acnehuatl.py` (commit fe49d65)
