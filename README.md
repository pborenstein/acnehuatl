# acnehuatl

**Āc nēhuātl?** — "Who am I?" (Nahuatl)

A small Python utility that answers the one question a model cannot reliably answer about itself: *which model am I, running in which harness, right now?*

The model is the least authoritative source on its own identity. The harness transcript is ground truth. Both pi and Claude Code record the actual invoked model on every assistant message in their session log files. `acnehuatl` reads those files directly. No introspection, no self-report.

## What it does

Given a working directory (cwd), `acnehuatl`:

1. **Detects the harness**: is this a pi session or a Claude Code session? (Based on which session directory exists for the cwd.)
2. **Finds the active session file**: the most recent `.jsonl` for that cwd.
3. **Reads the current model**: walks the session log to find what model is actually generating the current turn:
   - **pi:** the most recent `model_change` entry, falling back to the first assistant message's `provider`/`model`.
   - **Claude Code:** the most recent assistant message's `message.model` field.
4. **Returns** `(harness, provider, model)`.

## Usage

```bash
python3 acnehuatl.py                    # reports for the current cwd
python3 acnehuatl.py /path/to/vault     # reports for a given cwd
python3 acnehuatl.py --json             # machine-readable output
```

## Layout

- `acnehuatl.py` — the script (single file, stdlib only)
- `README.md` — this file
- `docs/` — project tracking (see below)

## Development Documentation

Project state is tracked in `docs/`:

- [`docs/CONTEXT.md`](docs/CONTEXT.md) — current session state; **read this first**
- [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) — phase progress tracker
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — architectural decisions (DEC-001..)
- [`docs/chronicles/`](docs/chronicles/) — session-by-session history

## Why

For the TOLTECAYOTL operator role: the same amanuensis is incarnated across models (Opus, glm-5.x, etc.). Provenance, which incarnation said what, matters for memoranda, zeitgeist, and any record of vault work. Self-attribution is unreliable; the transcript is not.

Future: a thin shim that skills (memorandum, vault-wrapup) call to stamp their output with the real incarnation, instead of the generic "Claude" label the memorandum skill currently defaults to.
