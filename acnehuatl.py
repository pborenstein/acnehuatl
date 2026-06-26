#!/usr/bin/env python3
"""
acnehuatl — Āc nēhuātl? "Who am I?"

Identify the current harness + model by reading the session transcript,
NOT by asking the model (which cannot reliably self-attribute).

pi and Claude Code write a JSONL session log keyed by cwd; each assistant
message records the model that actually generated it. opencode stores its
ground truth in a SQLite DB instead: its ~/.claude/ JSONL hardcodes a fake
model for compatibility (see DEC-006). This script reads the right source
per harness and reports it.

Usage:
    acnehuatl.py [--json | --label]

    --json   emit JSON instead of human-readable text
    --label  emit a single line: provider/model (harness)
             nothing else, no trailing text. Intended to be captured
             verbatim by a caller, e.g. LABEL=$(acnehuatl.py --label).
             Exits non-zero (and prints nothing) if the model cannot
             be determined — callers should treat that as fatal and
             never substitute a guessed value.

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
OPENCODE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def _detect_from_env():
    """Ground-truth harness detection from the process environment.

    The harness sets env vars that the model process inherits. These are
    authoritative — no guessing from filesystem mtimes.

    pi:           PI_CODING_AGENT (set to "true"), PI_CODING_AGENT_DIR,
                  PI_CODING_AGENT_SESSION_DIR
    Claude Code:  CLAUDE_CODE_*  (a whole family; any one implies CC)
    opencode:     OPENCODE=1 (or OPENCODE_PID, OPENCODE_RUN_ID, etc.)
    Crush:        CRUSH=1 (also AGENT=crush / AI_AGENT=crush)
    """
    # Crush sets CRUSH=1 (and AGENT/AI_AGENT=crush)
    if os.environ.get("CRUSH") or os.environ.get("AGENT") == "crush" or os.environ.get("AI_AGENT") == "crush":
        return "crush"
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

    Detection is env-var-only and authoritative. If no harness env var is
    set we cannot know which harness is running THIS process: the filesystem
    only shows which sessions exist for this cwd, not which one is current.
    Guessing would risk reporting a stale or other harness, so we return
    (None, None) and let the caller report the cwd as unknown. Never report
    a harness/model we are not sure is correct.
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
        # opencode ground truth is the SQLite DB, not a session dir. The
        # dir is unused for opencode; read_opencode() queries the DB by cwd.
        return ("opencode", None)

    if harness == "crush":
        # Crush ground truth is a per-project SQLite DB at <cwd>/.crush/crush.db.
        # The dir is unused for crush; read_crush() opens the DB by cwd.
        return ("crush", None)

    if harness == "claude-code":
        return ("claude-code", _find_session_dir(CC_DEFAULT_DIR, cwd))

    # No env signal — we cannot know which harness is running THIS process.
    # The filesystem only shows which sessions exist for this cwd, not which
    # one is current, so guessing would risk reporting a stale harness (this
    # is how a leftover pi session dir would be misreported under another
    # harness). Return unknown; the caller still reports the cwd.
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


# Minimal: only model prefixes we've actually observed in real sessions.
# Unknown prefixes -> None -> 'unknown', rather than guessing a provider
# string we haven't validated. Grows as new real cases appear.
PROVIDER_BY_MODEL = {
    "claude": "anthropic",
    "glm":    "z.ai",
}


def _infer_provider(model):
    """Derive a provider from the model name. Returns None if unrecognized.

    Claude Code carries no provider field in its transcript, so the provider
    is derived from the model prefix where possible.
    """
    if not model:
        return None
    head = model.split("-")[0].lower()
    return PROVIDER_BY_MODEL.get(head)


def read_claude_code(session_file: Path):
    """
    Claude Code session JSONL. Assistant messages carry:
        message.model  (e.g. "claude-sonnet-4-6", "glm-5.2")
    No explicit provider field exists in the transcript, so provider is
    DERIVED from the model prefix (see _infer_provider) — never assumed.
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
    provider = _infer_provider(model)   # derived, not read
    return (provider, model)


def read_opencode(cwd: str):
    """Read the real model from opencode's SQLite session DB.

    opencode stores ground truth in ~/.local/share/opencode/opencode.db.
    The `session` table has a `model` column holding JSON:
        {"id": "glm-5.2", "providerID": "zai-coding-plan", "variant": "default"}
    The `~/.claude/` JSONL is NOT ground truth for opencode (DEC-006); it
    hardcodes "claude-sonnet-4-6".

    Returns (provider, model, session_id). Any may be None if not found.
    """
    import sqlite3
    if not OPENCODE_DB.is_file():
        return (None, None, None)
    try:
        # Read-only, parameterized: no writes, no injection.
        con = sqlite3.connect(f"file:{OPENCODE_DB}?mode=ro", uri=True)
        row = con.execute(
            "SELECT model, id FROM session WHERE directory = ? "
            "ORDER BY time_updated DESC LIMIT 1",
            (cwd,),
        ).fetchone()
        con.close()
    except sqlite3.Error:
        return (None, None, None)
    if not row:
        return (None, None, None)
    model_json, session_id = row
    try:
        m = json.loads(model_json)
    except (json.JSONDecodeError, TypeError):
        return (None, None, session_id)
    return (m.get("providerID"), m.get("id"), session_id)


def read_crush(cwd: str):
    """Read the real model from Crush's per-project SQLite session DB.

    Crush stores a session DB at <cwd>/.crush/crush.db. The `messages` table
    has `model` and `provider` columns per assistant message; the current
    model is the most recent assistant message's model in the latest session.
    Like opencode (DEC-006), the DB is ground truth, not any JSONL.

    Returns (provider, model, session_id). Any may be None if not found.
    """
    import sqlite3
    db = Path(cwd) / ".crush" / "crush.db"
    if not db.is_file():
        return (None, None, None)
    try:
        # Read-only, parameterized: no writes, no injection.
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        srow = con.execute(
            "SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        if not srow:
            con.close()
            return (None, None, None)
        session_id = srow[0]
        mrow = con.execute(
            "SELECT provider, model FROM messages "
            "WHERE session_id = ? AND role = 'assistant' AND model != '' "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        con.close()
    except sqlite3.Error:
        return (None, None, None)
    if not mrow:
        return (None, None, session_id)
    return (mrow[0], mrow[1], session_id)


# ---------- entry point ----------

def identify():
    """
    Returns a dict:
      {harness, provider, model, provider_source, session_file, cwd}
    harness/provider/model may be None if undeterminable. provider_source is
    "read" (from the transcript/DB), "derived" (inferred from the model name,
    Claude Code only), or None when no provider could be determined.
    """
    cwd = os.getcwd()
    harness, session_dir = detect_harness_session_dir(cwd)
    result = {"harness": harness, "provider": None, "model": None,
              "provider_source": None, "session_file": None, "cwd": cwd}
    if harness is None:
        return result

    if harness == "opencode":
        provider, model, session_id = read_opencode(cwd)
        result["provider"] = provider
        result["provider_source"] = "read" if provider else None
        result["model"] = model
        result["session_file"] = session_id
        return result

    if harness == "crush":
        provider, model, session_id = read_crush(cwd)
        result["provider"] = provider
        result["provider_source"] = "read" if provider else None
        result["model"] = model
        result["session_file"] = session_id
        return result

    sf = _latest_session(session_dir)
    result["session_file"] = str(sf) if sf else None
    if sf is None:
        return result
    if harness == "pi":
        provider, model = read_pi(sf)
        result["provider_source"] = "read" if provider else None
    else:
        provider, model = read_claude_code(sf)
        result["provider_source"] = "derived" if provider else None
    result["provider"] = provider
    result["model"] = model
    return result


def _safe(s: str) -> str:
    return "".join(c if c.isprintable() else "" for c in s)


def label(result: dict):
    """Return the canonical incarnation string 'provider/model (harness)',
    or None if the model could not be determined.

    This is the single source of truth for the incarnation label. Callers
    must capture it verbatim and never reconstruct or guess it.
    """
    model = result.get("model")
    if not model:
        return None
    provider = result.get("provider") or "unknown"
    harness = result.get("harness") or "unknown"
    return f"{provider}/{model} ({harness})"


def _emit(result: dict, as_json: bool):
    if as_json:
        print(json.dumps(result, indent=2))
        return
    h = _safe(result.get("harness") or "(unknown harness)")
    p = _safe(result.get("provider") or "(unknown provider)")
    if result.get("provider_source") == "derived" and result.get("provider"):
        p = f"{p} (derived)"
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
    as_label = False
    for a in argv[1:]:
        if a == "--json":
            as_json = True
        elif a == "--label":
            as_label = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
    result = identify()

    if as_label:
        # Label mode: print ONLY the canonical incarnation string, and only
        # if it could be determined. On failure print nothing to stdout so a
        # caller using $(...) gets an empty string and a non-zero exit — it
        # must stop rather than substitute a guess.
        lbl = label(result)
        if lbl is None:
            if not result.get("session_file"):
                return 1
            return 2
        print(lbl)
        return 0

    _emit(result, as_json)
    if result.get("model"):
        return 0
    if not result.get("session_file"):
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
