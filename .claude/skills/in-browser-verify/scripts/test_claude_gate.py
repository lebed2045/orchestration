import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


HERE = Path(__file__).parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), HERE / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load("claude_in_browser_gate.py")
runner = _load("in_browser_verify.py")


class ClaudeGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        runner.init_repo(self.root)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def tearDown(self):
        self.temp.cleanup()

    def _invoke(self, event):
        stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(event))
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = gate.main()
        finally:
            sys.stdin = stdin
        self.assertEqual(code, 0)
        return json.loads(out.getvalue())

    def _transcript(self, text):
        # Real transcripts live outside the repo (~/.claude/projects/...), so they
        # must not perturb the workspace fingerprint.
        path = Path(self.temp.name).parent / f"transcript-{id(self)}.jsonl"
        self.addCleanup(path.unlink, missing_ok=True)
        entry = {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return str(path)

    def test_session_start_injects_contract(self):
        result = self._invoke({"hook_event_name": "SessionStart", "cwd": str(self.root)})
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("IN-BROWSER-VERIFY IS ACTIVE", context)

    def test_non_onboarded_repo_is_ignored(self):
        with tempfile.TemporaryDirectory() as other:
            result = self._invoke({"hook_event_name": "Stop", "cwd": other,
                                   "transcript_path": self._transcript("all done")})
        self.assertEqual(result, {"continue": True})

    def test_stop_without_completion_claim_continues(self):
        result = self._invoke({"hook_event_name": "Stop", "cwd": str(self.root),
                               "transcript_path": self._transcript("still investigating the issue")})
        self.assertEqual(result, {"continue": True})

    def test_stop_with_completion_claim_and_no_manifest_blocks(self):
        result = self._invoke({"hook_event_name": "Stop", "cwd": str(self.root),
                               "transcript_path": self._transcript("Feature implemented, everything works.")})
        self.assertEqual(result["decision"], "block")
        self.assertIn("WEB_VERIFICATION", result["reason"])

    def test_stop_with_fresh_passed_manifest_continues(self):
        run_dir = self.root / runner.RUNS_REL / "r1"
        run_dir.mkdir(parents=True)
        manifest = {"status": "passed", "workspace_fingerprint": runner.workspace_fingerprint(self.root)}
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = self._invoke({"hook_event_name": "Stop", "cwd": str(self.root),
                               "transcript_path": self._transcript("Feature implemented, everything works.")})
        # Manifest write is excluded from the fingerprint, so it stays valid.
        self.assertEqual(result, {"continue": True})

    def test_stop_hook_active_stops_with_reason(self):
        result = self._invoke({"hook_event_name": "Stop", "cwd": str(self.root), "stop_hook_active": True,
                               "transcript_path": self._transcript("done")})
        self.assertFalse(result["continue"])
        self.assertIn("unproven", result["stopReason"])


if __name__ == "__main__":
    unittest.main()
