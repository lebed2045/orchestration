#!/usr/bin/env python3
"""Codex SessionStart/Stop hook for repositories using in-browser-verify."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path


COMPLETION_RE = re.compile(
    r"\b(done|fixed|implemented|complete|completed|working|works|verified|passes|ready|resolved)\b",
    re.IGNORECASE,
)


def _load_runner():
    path = Path(__file__).with_name("in_browser_verify.py")
    spec = importlib.util.spec_from_file_location("in_browser_verify_hook_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _emit(data: dict) -> int:
    print(json.dumps(data))
    return 0


def _latest_manifest(root: Path) -> tuple[dict | None, Path | None]:
    paths = sorted((root / ".agent-verification/runs").glob("*/manifest.json"))
    if not paths:
        return None, None
    path = paths[-1]
    try:
        return json.loads(path.read_text(encoding="utf-8")), path
    except (OSError, json.JSONDecodeError):
        return None, path


def _verification_root(cwd: Path) -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if proc.returncode == 0:
        candidate = Path(proc.stdout.strip()).resolve()
        if (candidate / ".agent-verification/config.json").is_file():
            return candidate
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".agent-verification/config.json").is_file():
            return candidate
    return cwd


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return _emit({"continue": True, "systemMessage": "in-browser-verify hook received invalid JSON"})
    root = _verification_root(Path(event.get("cwd") or ".").resolve())
    if not (root / ".agent-verification/config.json").is_file():
        return _emit({"continue": True})

    event_name = event.get("hook_event_name")
    if event_name == "SessionStart":
        return _emit({
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "IN-BROWSER-VERIFY IS ACTIVE FOR THIS REPOSITORY. For every web feature or bug fix, "
                    "use $in-browser-verify: update the scenario ledger before implementation, add a RED "
                    "Playwright regression, run the complete gate, inspect the real flow in the "
                    "browser, and cite a successful manifest. Do not ask the user to restate recorded scenarios."
                ),
            },
        })
    if event_name != "Stop":
        return _emit({"continue": True})

    message = event.get("last_assistant_message") or ""
    if not COMPLETION_RE.search(message):
        return _emit({"continue": True})
    if event.get("stop_hook_active"):
        return _emit({
            "continue": False,
            "stopReason": "in-browser-verify remains unproven after one automatic continuation",
            "systemMessage": "WEB_VERIFICATION remains UNVERIFIED; report the missing proof explicitly.",
        })

    runner = _load_runner()
    manifest, manifest_path = _latest_manifest(root)
    current = runner.workspace_fingerprint(root)
    valid = bool(
        manifest
        and manifest.get("status") == "passed"
        and manifest.get("workspace_fingerprint") == current
    )
    if valid:
        return _emit({"continue": True})
    reason = (
        "WEB_VERIFICATION is missing or stale for the current workspace. Use $in-browser-verify now: "
        "update scenarios/tests, run the complete gate, inspect the live browser flow, and cite "
        "the passed manifest before making a completion claim."
    )
    if manifest_path:
        reason += f" Latest manifest: {manifest_path}"
    return _emit({"decision": "block", "reason": reason})


if __name__ == "__main__":
    raise SystemExit(main())
