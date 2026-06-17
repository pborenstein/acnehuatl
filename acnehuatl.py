#!/usr/bin/env python3
"""
acnehuatl — Āc nēhuātl? "Who am I?"

Identify the current harness + model by reading the session transcript,
NOT by asking the model (which cannot reliably self-attribute).

Both pi and Claude Code write a JSONL session log keyed by cwd. Each
assistant message records the model that actually generated it. This
script reads those files and reports ground truth.

Usage:
    acnehuatl.py [--json]

    --json  emit JSON instead of human-readable text

Exit codes:
    0  found
    1  no session found for cwd
    2  session found but no model could be read
"""

import json
import os
import sys
from pathlib import Path


# ---------- cwd -> session dir naming ----------

def _session_key(cwd: str) -> str:
    """Encode a cwd into the harness's session-dir name.

    Both pi and Claude Code encode path separators. Empirically the
    encoding is: replace each '/' with '-'. e.g.
        /Users/philip/x  ->  -Users-philip-x
    In practice pi stores these with a doubled leading/trailing dash
    (--Users-...--); callers should match against the actual on-disk
    name when present. We construct the simple form and let the caller
    fall back to a substring match if exact match fails.
    """
    return cwd.replace("/", "-")


# ---------- harness detection ----------

PI_DEFAULT_DIR = Path.home() / ".pi" / "agent"
CC_DEFAULT_DIR = Path.home() / ".claude" / "projects"


def _detect_from_env():
    """Ground-truth harness detection from the process environment.

    The harness sets env vars that the model process inherits. These are
    authoritative — no guessing from filesystem mtimes.

    pi:           PI_CODING_AGENT (set to "true"), PI_CODING_AGENT_DIR,
                  PI_CODING_AGENT_SESSION_DIR
    Claude Code:  CLAUDE_CODE_*  (a whole family; any one implies CC)
    opencode:     OPENCODE=1 (or OPENCODE_PID, OPENCODE_RUN_ID, etc.)
    """
    # opencode sets OPENCODE=1 (and optionally other OPENCODE_* vars)
    if os.environ.get("OPENCODE") or os.environ.get("OPENCODE_PID") or os.environ.get("OPENCODE_RUN_ID"):
        return "opencode"
    # pi sets PI_CODING_AGENT=true (and optionally the dir/session vars)
    if os.environ.get("PI_CODING_AGENT") or os.environ.get("PI_CODING_AGENT_DIR") or os.environ.get("PI_CODING_AGENT_SESSION_DIR"):
        return "pi"
    # Claude Code sets many CLAUDE_CODE_* vars; presence of any implies CC.
    if any(k.startswith("CLAUDE_CODE_") or k == "CLAUDE_PROJECT_DIR" for k in os.environ):
        return "claude-code"
    return None


def detect_harness_session_dir(cwd: str):
    """Return (harness_name, session_dir_path) or (None, None).

    Detection order:
      1. Env vars (ground truth — which harness is THIS process running under)
      2. Filesystem fallback (which session dirs exist for this cwd)
    """
    harness = _detect_from_env()

    # pi may hand us the session dir directly via env
    pi_session_dir_env = os.environ.get("PI_CODING_AGENT_SESSION_DIR")
    pi_base = Path(os.environ.get("PI_CODING_AGENT_DIR") or PI_DEFAULT_DIR)
    pi_sessions_root = pi_base / "sessions"

    if harness == "pi":
        if pi_session_dir_env:
            sd = Path(pi_session_dir_env)
            if sd.is_dir():
                return ("pi", sd)
        return ("pi", _find_session_dir(pi_sessions_root, cwd))

    if harness == "opencode":
        return ("opencode", _find_session_dir(CC_DEFAULT_DIR, cwd))

    if harness == "claude-code":
        return ("claude-code", _find_session_dir(CC_DEFAULT_DIR, cwd))

    # No env signal — filesystem fallback (best effort, may be ambiguous)
    pi_found = _find_session_dir(pi_sessions_root, cwd)
    if pi_found:
        return ("pi", pi_found)
    cc_found = _find_session_dir(CC_DEFAULT_DIR, cwd)
    if cc_found:
        return ("claude-code", cc_found)
    return (None, None)


def _latest_session(session_dir):
    """Most recently modified .jsonl in the dir, or None."""
    if session_dir is None:
        return None
    try:
        return max(session_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    except ValueError:
        return None


def _find_session_dir(sessions_root: Path, cwd: str):
    """Find the session subdir under sessions_root for the given cwd.

    Harnesses encode the cwd into the dir name by replacing '/' with '-',
    but the exact on-disk form varies (single vs double dashes, trailing
    dashes). We try exact match first, then a forgiving match that collapses
    repeated dashes and ignores a trailing dash difference. Returns Path or None.
    """
    if not sessions_root.is_dir():
        return None
    key = _session_key(cwd)
    # 1. exact
    exact = sessions_root / key
    if exact.is_dir():
        return exact
    # 2. forgiving: collapse runs of dashes and compare
    def collapse(s: str) -> str:
        import re
        return re.sub(r"-+", "-", s).strip("-")
    target = collapse(key)
    for p in sessions_root.iterdir():
        if p.is_dir() and collapse(p.name) == target:
            return p
    return None


# ---------- readers ----------

def read_pi(session_file: Path):
    """
    pi session JSONL. Each assistant message has:
        message.provider, message.model
    Model switches are explicit:
        {"type": "model_change", "provider": "...", "modelId": "..."}
    The current model = the most recent model_change, else the first
    assistant message's model.
    """
    provider, model = None, None
    cur_provider, cur_model = None, None
    with session_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = e.get("type")
            if t == "model_change":
                cur_provider = e.get("provider") or cur_provider
                cur_model = e.get("modelId") or cur_model
            elif t == "message":
                m = e.get("message")
                if isinstance(m, dict) and m.get("role") == "assistant":
                    if provider is None:
                        provider = m.get("provider")
                        model = m.get("model")
                    # latest assistant message wins for "current"
                    cur_provider = m.get("provider") or cur_provider
                    cur_model = m.get("model") or cur_model
    # prefer the latest observed (model_change or assistant), fall back to first
    return (cur_provider or provider, cur_model or model)


def read_claude_code(session_file: Path):
    """
    Claude Code session JSONL. Assistant messages carry:
        message.model  (e.g. "claude-sonnet-4-6")
    No explicit provider field; provider is assumed "anthropic".
    The current model = the most recent assistant message's model.
    """
    model = None
    with session_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = e.get("message")
            if isinstance(m, dict) and m.get("role") == "assistant":
                mm = m.get("model")
                if mm:
                    model = mm  # last one wins
    return ("anthropic", model)


# ---------- entry point ----------

def identify():
    """
    Returns a dict:
      {harness, provider, model, session_file, cwd}
    harness/provider/model may be None if undeterminable.
    """
    cwd = os.getcwd()
    harness, session_dir = detect_harness_session_dir(cwd)
    result = {"harness": harness, "provider": None, "model": None,
              "session_file": None, "cwd": cwd}
    if harness is None:
        return result
    sf = _latest_session(session_dir)
    result["session_file"] = str(sf) if sf else None
    if sf is None:
        return result
    if harness == "pi":
        provider, model = read_pi(sf)
    else:
        provider, model = read_claude_code(sf)
    result["provider"] = provider
    result["model"] = model
    return result


def _safe(s: str) -> str:
    return "".join(c if c.isprintable() else "" for c in s)


def _emit(result: dict, as_json: bool):
    if as_json:
        print(json.dumps(result, indent=2))
        return
    h = _safe(result.get("harness") or "(unknown harness)")
    p = _safe(result.get("provider") or "(unknown provider)")
    m = _safe(result.get("model") or "(unknown model)")
    sf = _safe(result.get("session_file") or "(no session file)")
    cwd = result.get("cwd")
    print(f"harness:   {h}")
    print(f"provider:  {p}")
    print(f"model:     {m}")
    print(f"session:   {sf}")
    print(f"cwd:       {cwd}")


def main(argv):
    as_json = False
    for a in argv[1:]:
        if a == "--json":
            as_json = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
    result = identify()
    _emit(result, as_json)
    if result.get("model"):
        return 0
    if not result.get("session_file"):
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
