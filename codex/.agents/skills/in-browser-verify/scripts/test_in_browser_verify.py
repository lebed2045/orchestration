import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("in_browser_verify.py")
SPEC = importlib.util.spec_from_file_location("in_browser_verify", SCRIPT)
in_browser_verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(in_browser_verify)


class WebVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        in_browser_verify.init_repo(self.root)
        tests = self.root / "tests/e2e"
        tests.mkdir(parents=True)
        (tests / "core.spec.ts").write_text("// SCENARIO: CORE-001\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_init_never_overwrites_contract(self):
        scenario = self.root / "verification/scenarios.md"
        scenario.write_text("custom", encoding="utf-8")
        in_browser_verify.init_repo(self.root)
        self.assertEqual(scenario.read_text(encoding="utf-8"), "custom")

    def test_init_installs_project_local_hooks(self):
        hooks = json.loads((self.root / ".codex/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(hooks["hooks"]["SessionStart"]), 1)
        self.assertEqual(len(hooks["hooks"]["Stop"]), 1)
        command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertIn("$HOME/.codex/skills/in-browser-verify", command)

    def test_check_requires_every_scenario_marker(self):
        _, coverage, _ = in_browser_verify.check_repo(self.root)
        self.assertEqual(coverage["covered_count"], 1)
        (self.root / "verification/scenarios.md").write_text(
            "## CORE-001: One\n\n## CORE-002: Two\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(in_browser_verify.VerificationError, "CORE-002"):
            in_browser_verify.check_repo(self.root)

    def test_run_writes_passed_manifest_with_fresh_evidence(self):
        config_path = self.root / in_browser_verify.CONFIG_REL
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["commands"] = [{"name": "pass", "argv": ["true"]}]
        config["evidence"] = {"required_globs": ["test-results/**/trace.zip"], "minimum_files": 1}
        config_path.write_text(json.dumps(config), encoding="utf-8")

        evidence = self.root / "test-results/case/trace.zip"
        original = in_browser_verify._run_command

        def run_and_create(*args, **kwargs):
            result = original(*args, **kwargs)
            evidence.parent.mkdir(parents=True)
            evidence.write_bytes(b"trace")
            return result

        with mock.patch.object(in_browser_verify, "_run_command", side_effect=run_and_create):
            self.assertEqual(in_browser_verify.run_repo(self.root), 0)
        manifest = sorted((self.root / in_browser_verify.RUNS_REL).glob("*/manifest.json"))[-1]
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "passed")
        self.assertEqual(data["evidence"], ["test-results/case/trace.zip"])

    def test_run_fails_without_fresh_evidence(self):
        config_path = self.root / in_browser_verify.CONFIG_REL
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["commands"] = [{"name": "pass", "argv": ["true"]}]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        self.assertEqual(in_browser_verify.run_repo(self.root), 1)
        manifest = sorted((self.root / in_browser_verify.RUNS_REL).glob("*/manifest.json"))[-1]
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "failed")
        self.assertIn("evidence missing", data["failure"])

    def test_unchanged_old_evidence_is_not_fresh_even_with_future_mtime(self):
        config_path = self.root / in_browser_verify.CONFIG_REL
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["commands"] = [{"name": "pass", "argv": ["true"]}]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        evidence = self.root / "test-results/case/trace.zip"
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b"stale")
        import os
        import time
        future = time.time() + 3600
        os.utime(evidence, (future, future))
        self.assertEqual(in_browser_verify.run_repo(self.root), 1)

    def test_workspace_fingerprint_changes_with_source_but_ignores_manifests(self):
        source = self.root / "app.ts"
        source.write_text("one", encoding="utf-8")
        subprocess = __import__("subprocess")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        before = in_browser_verify.workspace_fingerprint(self.root)
        source.write_text("two", encoding="utf-8")
        after = in_browser_verify.workspace_fingerprint(self.root)
        self.assertNotEqual(before, after)
        run_file = self.root / in_browser_verify.RUNS_REL / "x/manifest.json"
        run_file.parent.mkdir(parents=True)
        run_file.write_text("{}", encoding="utf-8")
        self.assertEqual(after, in_browser_verify.workspace_fingerprint(self.root))


if __name__ == "__main__":
    unittest.main()
