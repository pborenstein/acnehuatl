# acnehuatl

`whoami` for coding agents

A small Python utility that identifies:

- the LLM provider
- the LLM model
- the harness that the model is running in


It's very difficult to get models to identify themselves reliably. Unless the model provides an identity in the system prompt, the model will just next-token predict what it's going to say. So when you ask "Which model are you?" it's very likely to say Claude or ChatGPT.

`acnehuatl` uses the information in the session logs that harnesses use. It's all external identification, no introspection.

## Usage

Have your code harness or tool run this command to have the model identify itself.

```bash
python3 acnehuatl.py          # human-readable output
python3 acnehuatl.py --json   # machine-readable output
```

## Examples

Claude as a harness:

```
$ claude --dangerously-skip-permissions -p "run /Users/philip/projects/nahuatl-PROJECTS/acnehuatl/acnehuatl.py"                                              
The script ran successfully. Output:

		```
		harness:   claude-code
		provider:  anthropic
		model:     claude-sonnet-4-6
		session:   /Users/philip/.claude/projects/-Users-philip-projects-nahuatl-PROJECTS-acnehuatl/176812f6-c3c3-494f-b91d-d203323233f6.jsonl
		cwd:       /Users/philip/projects/nahuatl-PROJECTS/acnehuatl
		```

It correctly identified itself: running under Claude Code, using `claude-sonnet-4-6`, and found the active session JSONL file for this working directory.
```

Pi as a coding agent:

```
$ pi -p "run /Users/philip/projects/nahuatl-PROJECTS/acnehuatl/acnehuatl.py"                                                                                 13:12:51
The script ran successfully. Output:

		```
		harness:   pi
		provider:  zai
		model:     glm-5.1
		session:   /Users/philip/.pi/agent/sessions/--Users-philip-projects-nahuatl-PROJECTS-acnehuatl--/2026-06-18T17-13-21-223Z_019edbb9-1847-73c2-8080-8b711371884b.jsonl
		cwd:       /Users/philip/projects/nahuatl-PROJECTS/acnehuatl
		```

It printed the current harness, provider, model, session path, and working directory.
```


## How it works

`acnehuatl` uses the current working directory to find the active session:

1. **Detects the harness**: pi, Claude Code, or opencode? (env vars first, filesystem fallback)
2. **Finds the active session**: the most recent `.jsonl` for this cwd (pi, Claude Code), or the SQLite session row for this cwd (opencode).
3. **Reads the current model**: walks the session record to find what model is actually generating the current turn:
   - **pi:** the most recent `model_change` entry, falling back to the first assistant message's `provider`/`model`.
   - **Claude Code:** the most recent assistant message's `message.model` field.
   - **opencode:** the `session.model` JSON column from `~/.local/share/opencode/opencode.db` (the `~/.claude/` JSONL opencode writes is not ground truth).
4. **Returns** `(harness, provider, model)`.


## Project layout

- `acnehuatl.py`: the script (single file, stdlib only)
- `README.md`: this file
- `docs/`: project tracking (see below)

## Development Documentation

`acnehuatl` uses [handoff](https://github.com/pborenstein/handoff), a collection of skills to track the project state is tracked in `docs/`:

- [`docs/CONTEXT.md`](docs/CONTEXT.md): current session state; Code harnesses: **read this first**
- [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md): phase progress tracker
- [`docs/DECISIONS.md`](docs/DECISIONS.md): architectural decisions (DEC-001..)
- [`docs/chronicles/`](docs/chronicles/): session-by-session history


## Who, what, why

The code was written by GLM-5.1 and GLM-5.2 running under `pi`. The need was all mine. 

_Āc nēhuātl_ is "who am I" in Nahuatl.

It's important to track provenance in my projects. I need to know whether a human or an LLM wrote a particular  chunk of text.

