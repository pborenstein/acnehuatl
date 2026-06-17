---
review: security
repo: pborenstein/acnehuatl
commit: d2e00ff (cwd arg removed), Finding 2 fix pending commit
original_commit: 9c60c4e (single commit at first review)
date: 2026-06-17
reviewer: glm-5.2 (pi), per the transcript; Finding 2 fix by claude-sonnet-4-6 (Claude Code)
overall: low-risk. Findings 1 and 2 resolved; what remains is documentation and minor cleanups.
revision: 4 (Finding 2 control-char strip implemented)
---

# Security Review: `pborenstein/acnehuatl`

**Repo shape:** single Python file (`acnehuatl.py`, ~265 lines), stdlib-only, plus docs. No deps, no config, no CI, no secrets in-tree.

**What it does:** reads the local harness session transcript (`~/.pi/...` or `~/.claude/projects/...`) to report which model is generating the current turn. Pure read-only inspection of JSONL. Inputs are env vars (set by the harness) and `os.getcwd()`. **No CLI arguments, no stdin.**

**Verdict: low-risk.** Nothing remotely exploitable, no dangerous primitives. After the cwd-arg removal (commit d2e00ff), the only externally-steerable read path is via harness-inherited env vars, which is a trusted input by design. Remaining findings are hardening and documentation.

> This review went through three versions. v1 was static-only and made three mistakes (corrected by running the tool). v2/v3 folded in the runtime corrections and the cwd-arg removal. The reasoning trail is preserved inline; see "Revision history" at the bottom.

---

## Finding 1 — Input surface (resolved in v3 by cwd-arg removal; was Low–Med)

**Status: resolved.** v1 flagged the positional `cwd` argument: an untrusted cwd could redirect the read to *another project's* existing session dir on the same host, leaking that session's path and model/provider strings. Commit d2e00ff removed the argument entirely — `identify()` now takes no args and uses `os.getcwd()` unconditionally:

```python
def identify():
    ...
    cwd = os.getcwd()
```

So the only ways left to steer which file gets read are:

1. **Calling-process cwd.** The caller controls `os.getcwd()` by `cd`-ing before invoking. But that's the caller's own choice of working directory — there's no "victim" session being read through this channel that the caller couldn't already read directly. The trust relationship is "tool reads a session belonging to wherever you ran it," which is the intended contract.
2. **Harness-inherited env vars** (`PI_CODING_AGENT_SESSION_DIR`, `PI_CODING_AGENT_DIR`, the `CLAUDE_CODE_*` family). These are set by the harness itself; an attacker who can set them is already inside the trust boundary and doesn't need acnehuatl to read session files. Not an external surface.

Residual recommendation (optional, low priority): if a downstream consumer ever wants defense-in-depth against a caller that runs the tool from an unexpected directory, the tool could refuse to operate when `os.getcwd()` doesn't have a session dir of its own and instead fall through to a different one. Not needed today; the current behavior (exit 1, "no session") is already honest and safe.

> **What was wrong in v1/v2:** v1 suggested "skip the forgiving dash-collapse match for argv cwds" as the fix. That would have broken pi entirely, because pi stores session dirs in a doubled-dash form (`--Users-...--`) and the forgiving match is the *only* codepath that resolves them. v2 caught that and retracted the suggestion. v3 makes it moot: there's no argv cwd to constrain. The right move was removing the argument, which is what happened.

---

## Finding 2 — Human-readable output emits raw model strings (resolved in v4)

**Status: resolved.** Both readers pull `message.model`, `message.provider`, `model_change.modelId`, etc. straight from the transcript and print them. `json.dumps` escapes correctly, so the `--json` path was always safe. But the human-readable path did `print(f"model: {m}")` raw. A transcript whose `model` field contained terminal control sequences (ANSI escapes, cursor moves) would be emitted straight to the terminal.

Fixed by adding `_safe()` which strips non-printable characters from transcript-sourced strings before human-readable output:

```python
def _safe(s: str) -> str:
    return "".join(c if c.isprintable() else "" for c in s)
```

Applied to harness, provider, model, and session_file in `_emit`. The `cwd` field is not filtered (it comes from `os.getcwd()`, not the transcript).

---

## Finding 3 — Forgiving dash-collapse match is load-bearing (Informational, demoted from Low)

**Demoted to informational** now that Finding 1 is resolved. The point still stands as a code-comprehension note: DEC-004 frames the forgiving collapsed-dash match as a convenience with "small risk of collision," but runtime shows it's **the only thing that makes pi work at all**. pi's on-disk form is `--Users-...--` (doubled); `_session_key` produces single-dash names; the exact match always misses; the forgiving match resolves every pi session.

The "collision between cwds that differ only by dash runs" risk DEC-004 acknowledges is no longer security-relevant (no attacker-controllable cwd), but it is a correctness footgun for legitimate users who happen to have two project paths that collapse to the same name. Worth a code comment near the forgiving branch stating it is required for pi, not a fallback, so nobody "cleans it up" and breaks the harness.

> **What was wrong in v1/v2:** both prior versions suggested the forgiving match could be skipped or constrained for security. It cannot be skipped at all. Now that the security motivation is gone, this finding is purely a "don't accidentally delete this" note.

---

## Finding 4 — No integrity check on the transcript being read (Informational, unchanged)

acnehuatl's entire value proposition is "the transcript is ground truth, the model is not." If an attacker can write to `~/.pi/.../*.jsonl` or `~/.claude/projects/...` (file permissions, a malicious hook, a shared home), they control acnehuatl's output and thus the provenance stamp downstream skills trust. The code can't defend against a compromised home dir, but:
- Consider `os.stat`/permission awareness: warn (not fail) if the session file is world-writable or not owned by the current user. Cheap signal that the "ground truth" has been tampered with.
- Document this trust boundary explicitly. README/DEC-001 assert transcript = ground truth without naming that the transcript is only as trustworthy as the dir perms on `~/.pi` and `~/.claude`.

---

## Finding 5 — Hygiene (Informational, unchanged)

- `_detect_from_env` treats *any* `CLAUDE_CODE_*` env var as authoritative for harness selection. Low impact (just changes which reader runs), but "any var in a family implies X" is a weaker signal than checking a specific sentinel. Worth a comment.
- `read_claude_code` hardcodes `provider = "anthropic"` and ignores any provider signal. Correctness note, not security, but since the tool's job is accurate provenance, a wrong/hardcoded provider is a silent integrity degradation. Flag for the planned shim work.
- No `if __name__` guard issues, no `eval`/`exec`/`pickle`/`subprocess`/`os.system`. Clean on the dangerous-primitives axis.
- Exception handling: malformed JSONL lines are silently `continue`d (good). But `_latest_session` / `open` raise `PermissionError` / `OSError` on protected files and propagate uncaught to a traceback. Wrap reads in try/except and return the structured `(unknown)` result instead of crashing — nicer UX and avoids leaking the denied path via a traceback.
- `git log` now has real history; commit signing / tagged releases would still be load-bearing once skills trust the output. Process note, not code.

---

## Summary table (v4)

| # | Finding | Severity | Fix effort |
|---|---------|----------|-----------|
| 1 | ~~cwd arg path-steering~~ | **Resolved** (cwd removed) | n/a |
| 2 | ~~Raw model strings in human output~~ | **Resolved** (`_safe()` strip) | n/a |
| 3 | Forgiving dash-match is load-bearing for pi (demoted; correctness note now) | Info | Comment |
| 4 | Transcript trusted at file-perm level, undocumented | Info | Doc + optional perm check |
| 5 | Hardcoded anthropic provider; broad `CLAUDE_CODE_*` sentinel; uncaught OSErrors | Info | Small cleanups |

**Net:** Nothing exploitable remains. No externally-controllable input at all: the tool reads files derived from `os.getcwd()` and harness-inherited env vars, both trusted inputs by the threat model. Human-readable output now strips non-printables. The remaining work is documentation (4) and minor cleanups (3, 5). Ship-able as a provenance shim today.

---

## Runtime verification

Ran the tool from inside `/Users/philip/Obsidian/amoxtli`.

- **Default invocation (`python3 acnehuatl.py`):** exit 0, reported `provider: zai, model: glm-5.2`, correct session-file path. **End-to-end works.**
- **Encoding probe:** `_session_key('/Users/philip/Obsidian/amoxtli')` → `'-Users-philip-Obsidian-amoxtli'` (single dashes). On-disk dir is `'--Users-philip-Obsidian-amoxtli--'` (doubled). Exact match fails; forgiving collapsed-dash match resolves it. **This is why the forgiving match cannot be removed.**

Three claims from the static-only v1 were wrong and drove the v2/v3 corrections:
1. v1 implied the exact match was the normal path and the forgiving match a fallback. Inverted for pi: forgiving is the only path that works.
2. v1's proposed fix for Finding 1 ("skip forgiving match for argv cwds") would break pi. Retracted in v2.
3. v1's Finding 3 framed the forgiving match as removable hardening. It is load-bearing.

Lesson: the docstring of `_session_key` itself flags the doubled-dash form and says "callers should match against the actual on-disk name when present" — a static read that stopped at the docstring instead of running the code missed that the code then fails to do what the docstring warns about. Run the thing.

### Addendum: the reviewer was the subject, and missed it

The audit was conducted from inside `/Users/philip/Obsidian/amoxtli` — that directory's pi session *is* the session the reviewer (this model) was running in. When the tool reported `provider: zai, model: glm-5.2`, it was reporting the reviewer's own identity, not a demo corpus. The reviewer initially framed this as "end-to-end works ✓" and moved on, instead of registering that the tool had just answered — correctly, from ground truth — a question the reviewer could not answer about itself.

Re-checking the transcript confirms it: the trailing ~12 assistant turns are all stamped `zai / glm-5.2`, no recent `model_change`. So per the only available ground truth, the reviewer is glm-5.2 (confirmed separately by the user). There was no mismatch to chase; the tool was simply right, and the reviewer's instinct was to treat self-relevant output as a curiosity rather than a fact about itself.

This is arguably the strongest possible validation of DEC-001 ("read the transcript, not the model"): the model doing the review had no grounded self-knowledge, deflected when handed that knowledge, and the transcript was correct the whole time. Any downstream skill that calls acnehuatl to stamp provenance will get the right answer and, unlike the reviewer, will not be in a position to second-guess it.

---

## Revision history

- **v1 (commit 9c60c4e):** static read only. Three mistakes (above). Rated Finding 1 Low–Med, proposed fix that would have broken pi.
- **v2:** ran the tool. Corrected the three mistakes inline, retracted the bad fix, narrowed Finding 1 to "another project's existing session on the same host." Still rated Finding 1 the one thing worth fixing.
- **v3 (after commit d2e00ff):** cwd argument removed upstream. Finding 1 resolved outright. Finding 3 demoted to informational. Summary table updated; the only change still worth making before trusting the output is the Finding 2 control-char strip.
- **v4 (this version):** Finding 2 resolved. Added `_safe()` to strip non-printable characters from transcript-sourced strings in human-readable output. Both actionable findings now closed; only informational items remain.
