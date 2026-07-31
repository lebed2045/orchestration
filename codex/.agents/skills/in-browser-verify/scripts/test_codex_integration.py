import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
HOOK = HERE / "codex_in_browser_gate.py"
INSTALLER = HERE / "install_codex.py"
RUNNER = HERE / "in_browser_verify.py"
RUNNER_SPEC = importlib.util.spec_from_file_location("in_browser_verify_integration", RUNNER)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(runner)


def run_hook(root: Path, event: str, **extra):
    payload = {"cwd": str(root), "hook_event_name": event, **extra}
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return json.loads(proc.stdout)


class CodexIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        config = self.root / ".agent-verification/config.json"
        config.parent.mkdir(parents=True)
        config.write_text("{}", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_session_start_injects_contract(self):
        result = run_hook(self.root, "SessionStart")
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("$in-browser-verify", context)
        self.assertIn("scenario ledger", context)

    def test_stop_blocks_unverified_completion_claim(self):
        result = run_hook(self.root, "Stop", last_assistant_message="Implemented and ready.", stop_hook_active=False)
        self.assertEqual(result["decision"], "block")
        self.assertIn("missing or stale", result["reason"])

    def test_stop_ignores_non_completion_answer(self):
        result = run_hook(self.root, "Stop", last_assistant_message="Here is the requested explanation.", stop_hook_active=False)
        self.assertTrue(result["continue"])

    def test_stop_accepts_matching_passed_manifest_and_rejects_stale_one(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        source = self.root / "app.ts"
        source.write_text("one", encoding="utf-8")
        manifest = self.root / ".agent-verification/runs/one/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            "status": "passed",
            "workspace_fingerprint": runner.workspace_fingerprint(self.root),
        }), encoding="utf-8")
        accepted = run_hook(
            self.root, "Stop", last_assistant_message="Implemented and verified.",
            stop_hook_active=False,
        )
        self.assertTrue(accepted["continue"])
        source.write_text("two", encoding="utf-8")
        stale = run_hook(
            self.root, "Stop", last_assistant_message="Implemented and verified.",
            stop_hook_active=False,
        )
        self.assertEqual(stale["decision"], "block")

    def test_installer_is_idempotent(self):
        codex_home = self.root / "codex-home"
        env = {**os.environ, "CODEX_HOME": str(codex_home)}
        codex_home.mkdir(parents=True)
        old_command = "/usr/bin/python3 /tmp/in-browser-verify/scripts/codex_in_browser_gate.py"
        (codex_home / "hooks.json").write_text(json.dumps({"hooks": {
            "SessionStart": [{"hooks": [{"type": "command", "command": old_command}]}],
            "Stop": [{"hooks": [{"type": "command", "command": old_command}]}],
        }}), encoding="utf-8")
        for _ in range(2):
            subprocess.run([sys.executable, str(INSTALLER)], env=env, check=True, stdout=subprocess.PIPE, text=True)
        self.assertFalse((codex_home / "hooks.json").exists())
        self.assertTrue((codex_home / "skills/in-browser-verify").is_symlink())


if __name__ == "__main__":
    unittest.main()
