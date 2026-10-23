"""Exercise registration effects in real isolated homes, never the user's home."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "skills.py"
ARTIFACTS = ROOT / "codex" / "temp" / "skill-link-tests"


class SkillLinksTests(unittest.TestCase):
    def setUp(self):
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        self.case = Path(tempfile.mkdtemp(prefix="case-", dir=ARTIFACTS))
        self.root = self.case / "shared"
        self.home = self.case / "home"
        self.root.mkdir()
        self.home.mkdir()
        self.source = self.root / "sources" / "tldr"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text("---\nname: tldr\ndescription: Test summary\n---\nVersion one\n")
        self.target = self.home / ".agents" / "skills" / "tldr"
        self.registry = {"schema_version": 1, "skills": {"tldr": {
            "provider": "orchestration", "engines": {
                "codex": [{"source": "sources/tldr", "target": ".agents/skills/tldr", "kind": "skill"}],
                "claude": [{"source": "sources/tldr", "target": ".claude/skills/tldr", "kind": "skill"}]
            }}}}
        self.save_registry()
        (self.root / "dependencies.json").write_text('{"schema_version":1,"dependencies":[]}\n')

    def save_registry(self):
        (self.root / "skills.json").write_text(json.dumps(self.registry))

    def run_tool(self, command, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root),
            "--home", str(self.home), "--machine", "test-host", command, *args],
            text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def apply(self, *extra):
        result = self.run_tool("apply", "--engine", "codex", "--skill", "tldr", "--confirm", *extra)
        return json.loads(result.stdout)

    # Removing preview's read-only boundary would create paths in this fixture.
    def test_plan_and_inventory_do_not_write(self):
        before = sorted(str(p.relative_to(self.case)) for p in self.case.rglob("*"))
        result = self.run_tool("plan", "--engine", "codex", "--skill", "tldr")
        self.assertEqual(json.loads(result.stdout)["operations"][0]["state"], "missing")
        self.run_tool("inventory")
        self.assertEqual(before, sorted(str(p.relative_to(self.case)) for p in self.case.rglob("*")))

    # Missing explicit confirmation must not install even a first-party link.
    def test_apply_requires_confirmation_and_selection(self):
        self.assertNotEqual(self.run_tool("apply", "--engine", "codex", "--skill", "tldr", ok=False).returncode, 0)
        self.assertNotEqual(self.run_tool("apply", "--engine", "codex", "--confirm", ok=False).returncode, 0)
        self.assertFalse(self.target.exists())
        self.assertFalse((self.root / "global").exists())

    # Copying rather than linking would fail the update-through-source assertion.
    def test_apply_is_live_idempotent_and_reports_health(self):
        first = self.apply()
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(self.target.resolve(), self.source)
        (self.source / "SKILL.md").write_text("Updated in the other machine\n")
        self.assertEqual((self.target / "SKILL.md").read_text(), "Updated in the other machine\n")
        second = self.apply()
        self.assertIsNone(second["receipt"])
        self.assertEqual(len(list((self.root / "global" / "registrations").rglob("receipt.json"))), 1)
        state = self.run_tool("status", "--engine", "codex", "--skill", "tldr")
        self.assertEqual(json.loads(state.stdout)["operations"][0]["state"], "linked")
        self.assertIsNotNone(first["receipt"])

    # Applying one engine must not mutate the other tool's registration.
    def test_both_engines_read_the_same_source(self):
        data = json.loads(self.run_tool("apply", "--engine", "both", "--skill", "tldr", "--confirm").stdout)
        other = self.home / ".claude" / "skills" / "tldr"
        self.assertEqual(self.target.resolve(), other.resolve())
        self.assertEqual(len(data["changed"]), 2)

    # Clobbering an existing directory or losing its contents is a data-loss bug.
    def test_existing_directory_needs_replace_and_is_restorable(self):
        self.target.mkdir(parents=True)
        (self.target / "mine.txt").write_text("original")
        refused = self.run_tool("apply", "--engine", "codex", "--skill", "tldr", "--confirm", ok=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual((self.target / "mine.txt").read_text(), "original")
        receipt = self.apply("--replace")["receipt"]
        self.assertTrue(self.target.is_symlink())
        self.run_tool("restore", "--receipt", receipt, "--confirm")
        self.assertFalse(self.target.is_symlink())
        self.assertEqual((self.target / "mine.txt").read_text(), "original")

    # exists() alone misses dangling links and can overwrite the previous target.
    def test_dangling_link_is_preserved_and_restored(self):
        self.target.parent.mkdir(parents=True)
        self.target.symlink_to(self.case / "offline-share")
        receipt = self.apply("--replace")["receipt"]
        self.run_tool("restore", "--receipt", receipt, "--confirm")
        self.assertEqual(os.readlink(self.target), str(self.case / "offline-share"))

    # Restore must never overwrite a registration someone changed after apply.
    def test_restore_refuses_changed_target(self):
        receipt = self.apply()["receipt"]
        self.target.unlink()
        self.target.write_text("new user work")
        result = self.run_tool("restore", "--receipt", receipt, "--confirm", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.target.read_text(), "new user work")

    # An offline source must fail the entire preflight, before a second link exists.
    def test_missing_source_prevents_partial_apply(self):
        self.registry["skills"]["tldr"]["engines"]["codex"].append({
            "source": "sources/offline", "target": ".agents/skills/offline", "kind": "skill"})
        self.save_registry()
        result = self.run_tool("apply", "--engine", "codex", "--skill", "tldr", "--confirm", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())
        self.assertFalse((self.root / "global").exists())

    # Registry-controlled traversal must not write outside the chosen tool home.
    def test_registry_traversal_and_symlink_parents_are_rejected(self):
        entry = self.registry["skills"]["tldr"]["engines"]["codex"][0]
        entry["target"] = "../outside"
        self.save_registry()
        self.assertNotEqual(self.run_tool("plan", "--engine", "codex", "--skill", "tldr", ok=False).returncode, 0)
        entry["target"] = ".agents/skills/tldr"
        self.save_registry()
        elsewhere = self.case / "elsewhere"
        elsewhere.mkdir()
        (self.home / ".agents").symlink_to(elsewhere)
        self.assertNotEqual(self.run_tool("apply", "--engine", "codex", "--skill", "tldr", "--confirm", ok=False).returncode, 0)
        self.assertEqual(list(elsewhere.iterdir()), [])

    # A legacy copy would otherwise remain a second active discovery source.
    def test_legacy_duplicate_is_a_blocker(self):
        legacy = self.home / ".codex" / "skills" / "tldr"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("old version")
        result = self.run_tool("apply", "--engine", "codex", "--skill", "tldr", "--confirm", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())
        receipt = self.apply("--retire-legacy")["receipt"]
        self.assertFalse(legacy.exists())
        self.run_tool("restore", "--receipt", receipt, "--confirm")
        self.assertEqual((legacy / "SKILL.md").read_text(), "old version")

    # Requiring actual vendor approval prevents arbitrary new third-party activation.
    def test_unselected_dependency_cannot_be_registered(self):
        deps = {"schema_version": 1, "dependencies": [{"name": "superpowers", "source_directory": "vendor/superpowers/1", "skills_directory": "skills", "available_skills": ["review"], "selected_skills": []}]}
        (self.root / "dependencies.json").write_text(json.dumps(deps))
        source = self.root / "vendor" / "superpowers" / "1" / "skills" / "review"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("review")
        result = self.run_tool("apply", "--engine", "codex", "--skill", "superpowers:review", "--confirm", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / ".agents").exists())

    def test_reflection_routes_its_history_into_shared_tree(self):
        self.registry["skills"]["tldr"]["route_ledgers"] = True
        self.save_registry()
        original = self.home / ".codex" / "reflections"
        original.mkdir(parents=True)
        (original / "incidents.jsonl").write_text('old incident\n')
        receipt = self.apply("--replace")["receipt"]
        shared = self.root / "global/log/test-host-codex/reflections"
        self.assertTrue(original.is_symlink())
        self.assertEqual(original.resolve(), shared)
        self.assertEqual((original / "incidents.jsonl").read_text(), 'old incident\n')
        (original / "new.md").write_text('new incident')
        self.run_tool("restore", "--receipt", receipt, "--confirm")
        self.assertFalse(original.is_symlink())
        self.assertEqual((original / "incidents.jsonl").read_text(), 'old incident\n')
        self.assertEqual((shared / "new.md").read_text(), 'new incident')

    def test_divergent_shared_history_is_not_overwritten(self):
        self.registry["skills"]["tldr"]["route_ledgers"] = True
        self.save_registry()
        local = self.home / ".codex/reflections"
        local.mkdir(parents=True)
        (local / "incidents.jsonl").write_text('local')
        shared = self.root / "global/log/test-host-codex/reflections"
        shared.mkdir(parents=True)
        (shared / "incidents.jsonl").write_text('shared')
        result = self.run_tool("apply", "--engine", "codex", "--skill", "tldr", "--confirm", "--replace", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())
        self.assertEqual((local / "incidents.jsonl").read_text(), 'local')
        self.assertEqual((shared / "incidents.jsonl").read_text(), 'shared')

    def test_mid_apply_failure_restores_prior_targets(self):
        self.target.mkdir(parents=True)
        (self.target / 'mine').write_text('keep')
        spec = importlib.util.spec_from_file_location('skill_link_test_module', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        real_symlink = os.symlink
        calls = []
        def fail_second(source, target, *args, **kwargs):
            calls.append(target)
            if len(calls) == 2:
                raise OSError('injected filesystem failure')
            return real_symlink(source, target, *args, **kwargs)
        with mock.patch('os.symlink', side_effect=fail_second):
            with self.assertRaises(module.SetupError):
                module.apply(self.root, self.home, 'test-host', ('codex', 'claude'), ['tldr'], True, False, [])
        self.assertFalse(self.target.is_symlink())
        self.assertEqual((self.target / 'mine').read_text(), 'keep')
        self.assertFalse((self.home / '.claude/skills/tldr').exists())
        receipts = list((self.root / 'global/registrations').rglob('receipt.json'))
        self.assertEqual(json.loads(receipts[0].read_text())['status'], 'rolled_back')

    def test_selected_dependency_requires_a_verified_source_revision(self):
        deps = {"schema_version": 1, "dependencies": [{"name": "superpowers", "source_directory": "vendor/superpowers/1", "skills_directory": "skills", "commit": "a" * 40, "available_skills": ["review"], "selected_skills": ["review"]}]}
        (self.root / "dependencies.json").write_text(json.dumps(deps))
        source = self.root / "vendor/superpowers/1/skills/review"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("unverified source")
        result = self.run_tool("apply", "--engine", "codex", "--skill", "superpowers:review", "--confirm", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / ".agents").exists())

    def test_retirement_cannot_remove_another_selected_target(self):
        self.registry['skills']['other'] = {"provider": "orchestration", "legacy_targets": {"codex": [".agents/skills/tldr"]},
            "engines": {"codex": [{"source": "sources/tldr", "target": ".agents/skills/other", "kind": "skill"}]}}
        self.save_registry()
        result = self.run_tool("plan", "--engine", "codex", "--skill", "tldr", "--skill", "other", ok=False)
        self.assertNotEqual(result.returncode, 0)

    def test_linked_unselected_dependency_is_not_healthy(self):
        deps = {"schema_version": 1, "dependencies": [{"name": "superpowers", "source_directory": "sources", "skills_directory": ".", "available_skills": ["tldr"], "selected_skills": []}]}
        (self.root / "dependencies.json").write_text(json.dumps(deps))
        self.target.parent.mkdir(parents=True)
        self.target.symlink_to(self.source)
        result = self.run_tool("status", "--engine", "codex", "--skill", "superpowers:tldr", ok=False)
        self.assertNotEqual(result.returncode, 0)

    def test_dependency_root_cannot_redirect_outside_share(self):
        deps = {"schema_version": 1, "dependencies": [{"name": "superpowers", "source_directory": "vendor/escape", "skills_directory": ".", "commit": "a" * 40, "available_skills": ["tldr"], "selected_skills": ["tldr"]}]}
        (self.root / "dependencies.json").write_text(json.dumps(deps))
        (self.root / "vendor").mkdir()
        (self.root / "vendor/escape").symlink_to(self.case)
        spec = importlib.util.spec_from_file_location('skill_dependency_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module.subprocess, 'run') as run:
            result = module.dependency_integrity(self.root, deps['dependencies'][0])
        self.assertEqual(result['status'], 'unverified')
        run.assert_not_called()

    def test_same_home_mutation_lock_refuses_concurrent_apply(self):
        spec = importlib.util.spec_from_file_location('skill_link_lock_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.mutation_lock(self.root, self.home):
            result = self.run_tool('apply', '--engine', 'codex', '--skill', 'tldr', '--confirm', ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())

    def test_restore_failure_journals_progress_and_can_resume(self):
        self.target.mkdir(parents=True)
        (self.target / 'mine').write_text('preserve me')
        receipt = Path(self.apply('--replace')['receipt'])
        spec = importlib.util.spec_from_file_location('skill_restore_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual_move = module.shutil.move
        def fail_original_restore(source, target, *args, **kwargs):
            if Path(source).parent.name == 'backups':
                raise OSError('injected original restore failure')
            return actual_move(source, target, *args, **kwargs)
        with mock.patch.object(module.shutil, 'move', side_effect=fail_original_restore):
            with self.assertRaises(module.SetupError):
                module.restore(self.root, self.home, str(receipt))
        saved = json.loads(receipt.read_text())
        self.assertEqual(saved['status'], 'recovery_required')
        self.assertFalse(saved['operations'][0]['linked'])
        self.assertTrue(saved['operations'][0]['backed_up'])
        self.run_tool('restore', '--receipt', str(receipt), '--confirm')
        self.assertEqual((self.target / 'mine').read_text(), 'preserve me')

    def test_restore_resumes_after_an_earlier_item_was_fully_restored(self):
        self.target.mkdir(parents=True)
        (self.target / 'mine').write_text('first')
        other = self.home / '.claude/skills/tldr'
        other.mkdir(parents=True)
        (other / 'mine').write_text('second')
        result = self.run_tool('apply', '--engine', 'both', '--skill', 'tldr', '--replace', '--confirm')
        receipt = Path(json.loads(result.stdout)['receipt'])
        spec = importlib.util.spec_from_file_location('skill_restore_partial_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual_move = module.shutil.move
        def fail_later(source, target, *args, **kwargs):
            if Path(source).parent.name == 'backups' and Path(source).name == '0':
                raise OSError('later failure')
            return actual_move(source, target, *args, **kwargs)
        with mock.patch.object(module.shutil, 'move', side_effect=fail_later):
            with self.assertRaises(module.SetupError):
                module.restore(self.root, self.home, str(receipt))
        self.run_tool('restore', '--receipt', str(receipt), '--confirm')
        self.assertEqual((self.target / 'mine').read_text(), 'first')
        self.assertEqual((other / 'mine').read_text(), 'second')


if __name__ == "__main__":
    unittest.main()
