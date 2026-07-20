#!/usr/bin/env python3
"""Force non-interactive approval policy on Claude-to-Codex MCP calls."""

from __future__ import annotations

import json
import sys
from typing import Any


TARGET_TOOLS = {
    "mcp__codex-cli__codex",
    "mcp__codex-coder__codex",
}


def rewrite_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return Claude hook output, preserving the full original MCP input."""
    if (
        event.get("hook_event_name") != "PreToolUse"
        or event.get("tool_name") not in TARGET_TOOLS
    ):
        return {}

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        raise ValueError("Codex MCP tool_input must be a JSON object")

    updated_input = dict(tool_input)
    updated_input["approval-policy"] = "never"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": updated_input,
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
        output = rewrite_event(event)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Codex MCP policy hook blocked malformed input: {exc}", file=sys.stderr)
        return 2

    json.dump(output, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
