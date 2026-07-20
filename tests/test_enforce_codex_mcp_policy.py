#!/usr/bin/env python3

import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


HOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / ".claude"
    / "hooks"
    / "enforce_codex_mcp_policy.py"
)
SPEC = importlib.util.spec_from_file_location("enforce_codex_mcp_policy", HOOK_PATH)
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class CodexMcpPolicyHookTests(unittest.TestCase):
    def test_injects_never_and_preserves_complete_input(self):
        tool_input = {
            "prompt": "review",
            "cwd": "/tmp/project",
            "sandbox": "read-only",
            "config": {"model_reasoning_effort": "high"},
        }
        result = HOOK.rewrite_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "mcp__codex-cli__codex",
                "tool_input": tool_input,
            }
        )

        updated = result["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["approval-policy"], "never")
        self.assertEqual(
            {key: value for key, value in updated.items() if key != "approval-policy"},
            tool_input,
        )
        self.assertNotIn("approval-policy", tool_input)

    def test_overrides_interactive_policy_for_coder_server(self):
        result = HOOK.rewrite_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "mcp__codex-coder__codex",
                "tool_input": {
                    "prompt": "implement",
                    "approval-policy": "on-request",
                    "sandbox": "workspace-write",
                },
            }
        )

        updated = result["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["approval-policy"], "never")
        self.assertEqual(updated["sandbox"], "workspace-write")

    def test_ignores_other_tools(self):
        result = HOOK.rewrite_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "true"},
            }
        )

        self.assertEqual(result, {})

    def test_malformed_target_input_fails_closed(self):
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "mcp__codex-cli__codex",
                    "tool_input": "not-an-object",
                }
            )
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = HOOK.main()
        finally:
            sys.stdin = original_stdin

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("blocked malformed input", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
