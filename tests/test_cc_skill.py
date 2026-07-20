import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".claude" / "skills" / "cc" / "SKILL.md"
WORKFLOW_PATH = ROOT / ".claude" / "commands" / "workflow.md"
README_PATH = ROOT / "README.md"
CLAUDE_PATH = ROOT / "CLAUDE.md"
MCP_PATH = ROOT / ".mcp.json"


class CcSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL_PATH.read_text()
        cls.workflow = WORKFLOW_PATH.read_text()
        cls.readme = README_PATH.read_text()
        cls.claude = CLAUDE_PATH.read_text()
        cls.mcp = json.loads(MCP_PATH.read_text())

    def test_skill_is_user_invocable_and_standalone(self):
        self.assertRegex(self.skill, r"(?m)^name: cc$")
        self.assertRegex(self.skill, r"(?m)^description: .+invokes /cc.+$")
        self.assertIn("**Updated:** `20-jul-2026`", self.skill)
        self.assertIn("Treat the text after `/cc` as the task.", self.skill)
        self.assertIn("Do not invoke `/wf`", self.skill)
        self.assertNotIn("`/wf -cc", self.skill)

    def test_codex_owns_tests_implementation_fixes_and_cops(self):
        for required in (
            "Use Codex to author the plan, the failing tests, the implementation, and every fix iteration.",
            "RED call:",
            "GREEN call:",
            "## 4. Codex cops",
            "mcp__codex-coder__codex-reply",
        ):
            self.assertIn(required, self.skill)

        self.assertGreaterEqual(
            self.skill.count("mcp__codex-coder__codex({"),
            2,
            "RED and GREEN must both use the dedicated Codex coder",
        )
        self.assertIn('sandbox: "workspace-write"', self.skill)
        self.assertIn('sandbox: "read-only"', self.skill)

    def test_both_gates_are_claude_reviews_of_codex_artifacts(self):
        # Gate 1: Codex authors the plan, Claude independently reviews it.
        self.assertRegex(
            self.skill,
            r"(?s)## 2\. Codex plan and Gate 1.+Gate 1 is Claude's own independent review of Codex's plan",
        )
        # Gate 2: a fresh Claude agent reviews Codex's code.
        self.assertRegex(
            self.skill,
            r"(?s)## 5\. Gate 2: fresh Claude code review.+Codex must not be the final reviewer of its own implementation",
        )
        self.assertIn("different fresh Claude reviewer", self.skill)
        # Claude must not author the plan (that would make Gate 1 a self-review).
        self.assertNotIn("Claude writes a concise plan", self.skill)
        self.assertIn("Use Codex to author the plan", self.skill)

    def test_failed_codex_coding_never_falls_back_to_claude(self):
        self.assertIn("Never retry it through a Claude coder", self.skill)
        self.assertIn("hard-stop with all state preserved", self.skill)
        self.assertIn("git worktree remove --force <exact-path>", self.skill)
        self.assertIn("If safe isolation cannot be proven, preserve the worktree", self.skill)

    def test_dedicated_coder_mcp_has_long_timeout(self):
        server = self.mcp["mcpServers"]["codex-coder"]
        self.assertEqual(server["type"], "stdio")
        self.assertEqual(server["command"], "codex")
        self.assertEqual(server["args"], ["mcp-server"])
        self.assertGreater(server["timeout"], 300_000)
        self.assertEqual(server["timeout"], 1_800_000)

        install = (
            "claude mcp add-json --scope user codex-coder "
            '\'{"type":"stdio","command":"codex","args":["mcp-server"],'
            '"timeout":1800000}\''
        )
        self.assertIn(install, self.readme)

    def test_workflow_has_no_cc_flag(self):
        self.assertNotRegex(self.workflow, r"(?<![A-Za-z0-9])-cc(?![A-Za-z0-9])")
        self.assertNotRegex(self.claude, r"(?<![A-Za-z0-9])-cc(?![A-Za-z0-9])")
        self.assertNotRegex(self.readme, r"(?<![A-Za-z0-9])-cc(?![A-Za-z0-9])")


if __name__ == "__main__":
    unittest.main()
