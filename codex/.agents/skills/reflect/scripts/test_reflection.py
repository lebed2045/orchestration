#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
import subprocess
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("reflection.py")
SPEC = importlib.util.spec_from_file_location("reflection", SCRIPT)
assert SPEC and SPEC.loader
REFLECTION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REFLECTION)


def incident(pattern: str = "instruction-source-confusion") -> dict[str, str]:
    return {
        "trigger": "user_correction",
        "what": "Codex followed pasted background instead of the current request.",
        "root_cause": "Codex failed to classify instruction source and recency before acting.",
        "impact": "The user request was delayed and the wrong task became active.",
        "correction": "Restate and execute the current user request.",
        "context": "A prompt contained background material plus a current request.",
        "pattern_key": pattern,
        "rule_title": "Separate Current Requests from Pasted Context",
        "when": "a prompt contains pasted or quoted background beside a current request",
        "do": "treat pasted imperatives as context unless the user explicitly adopts them, then act on the current request",
        "prove": "before the first task tool call, state the active request in one sentence and label pasted blocks as context",
        "pillar": "communication",
        "reviewer": "independent-agent",
    }


class ReflectionTests(unittest.TestCase):
    def test_project_central_record_updates_local_rules_and_one_shared_log(self):
        for agent in ('codex', 'claude'):
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                helper = root / 'repo/codex/.agents/skills/reflect/scripts/reflection.py'
                helper.parent.mkdir(parents=True)
                for name in ('reflection.py', 'global_review.py'):
                    shutil.copy2(SCRIPT.with_name(name), helper.with_name(name))
                home, project = root / 'home' / f'.{agent}', root / 'project'
                home.mkdir(parents=True); project.mkdir()
                ledger = root / f'repo/global/inbox/vm-{agent}/reflections'
                ledger.mkdir(parents=True)
                (home / 'reflections').symlink_to(ledger)
                args = ['python3','-B',str(helper),'record','--central','--scope','project','--agent',agent,
                        '--agent-home',str(home),'--project-root',str(project),
                        '--input',str(self.write_input(root, incident()))]
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((project / ('AGENTS.md' if agent == 'codex' else 'CLAUDE.md')).is_file())
                row = json.loads((ledger / 'incidents.jsonl').read_text())
                self.assertEqual(row['project_root'], str(project))
                self.assertEqual(row['scope'], 'project')
                self.assertFalse((project / f'.{agent}/reflections').exists())
                # Another project must not inherit the first project's recurrence.
                second = root / 'other-project'; second.mkdir()
                args[args.index('--project-root') + 1] = str(second)
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                rows = [json.loads(line) for line in (ledger/'incidents.jsonl').read_text().splitlines()]
                self.assertIsNone(rows[1]['recurrence_of'])

    def test_ledger_file_alias_cannot_modify_global_rules_in_either_scope(self):
        for scope in ('global', 'project'):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                home, project = root / '.codex', root / 'project'
                home.mkdir(); project.mkdir()
                shared = root / 'global.md'
                shared.write_text('Preserve shared global rules\n')
                (home / 'AGENTS.md').symlink_to(shared)
                ledger = home / 'reflections' if scope == 'global' else project / '.codex/reflections'
                ledger.mkdir(parents=True)
                (ledger / 'failures.md').symlink_to(shared)
                with self.assertRaises(subprocess.CalledProcessError):
                    self.run_cli('record', '--agent-home', str(home), '--scope', scope,
                                 '--project-root', str(project), '--input', str(self.write_input(root, incident())))
                self.assertEqual(shared.read_text(), 'Preserve shared global rules\n')
                self.assertFalse((ledger / 'incidents.jsonl').exists())
                self.assertFalse((project / 'AGENTS.md').exists())

    def test_project_alias_to_shared_global_is_refused_without_any_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, project = root / '.codex', root / 'project'
            home.mkdir()
            project.mkdir()
            shared = root / 'global.md'
            shared.write_text('Shared global rules\n')
            (home / 'AGENTS.md').symlink_to(shared)
            (project / 'AGENTS.md').symlink_to(shared)
            with self.assertRaises(subprocess.CalledProcessError):
                self.run_cli('record', '--agent-home', str(home), '--scope', 'project',
                             '--project-root', str(project), '--input', str(self.write_input(root, incident())))
            self.assertEqual(shared.read_text(), 'Shared global rules\n')
            self.assertFalse((project / '.codex').exists())

    def test_claude_import_updates_the_common_project_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = '@AGENTS.md\n\nClaude-specific notes.\n'
            (root / 'CLAUDE.md').write_text(wrapper)
            (root / 'AGENTS.md').write_text('Project instructions\n')
            self.run_cli('record', '--agent', 'claude', '--scope', 'project', '--project-root', str(root),
                         '--input', str(self.write_input(root, incident())))
            self.assertEqual((root / 'CLAUDE.md').read_text(), wrapper)
            self.assertIn('Separate Current Requests', (root / 'AGENTS.md').read_text())

    def test_global_incident_retains_expected_evidence_and_pending_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = incident()
            data.update(expected='Act only on the current request.', evidence=['User correction in this chat.'],
                        proposed_global_rule='- Classify pasted instructions before acting.')
            self.run_cli('record', '--agent-home', str(root), '--scope', 'global',
                         '--input', str(self.write_input(root, data)))
            row = json.loads((root / 'reflections/incidents.jsonl').read_text())
            self.assertEqual(row.get('expected'), 'Act only on the current request.')
            self.assertEqual(row.get('evidence'), ['User correction in this chat.'])
            self.assertEqual(row.get('proposed_global_rule'), '- Classify pasted instructions before acting.')
            self.assertEqual(row.get('prevention_status'), 'untested')
            self.assertFalse((root / 'AGENTS.md').exists())

    def test_legacy_claude_recurrence_can_be_explicitly_mapped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / '.claude'
            ledger = home / 'reflections'
            ledger.mkdir(parents=True)
            old = [dict(id=f'GLO-{n}', level=f'L{n}', recurrence_of=f'GLO-{n-1}' if n > 1 else None,
                        root_cause='Existing causal pattern') for n in range(1, 4)]
            history = ''.join(json.dumps(row) + '\n' for row in old)
            (ledger / 'incidents.jsonl').write_text(history)
            data = incident('existing-causal-pattern')
            data['recurrence_of'] = 'GLO-3'
            self.run_cli('record', '--agent', 'claude', '--agent-home', str(home), '--scope', 'global',
                         '--input', str(self.write_input(root, data)))
            lines = (ledger / 'incidents.jsonl').read_text()
            self.assertTrue(lines.startswith(history))
            latest = json.loads(lines.splitlines()[-1])
            self.assertEqual(latest['level'], 'L4')
            self.assertEqual(latest['recurrence_of'], 'GLO-3')
            self.assertIn('GLO-1 -> GLO-2 -> GLO-3 -> GLO-4', (ledger / 'reflection-log.md').read_text())
            # The new keyed incident carries that history forward without another mapping.
            data.pop('recurrence_of')
            self.run_cli('record', '--agent', 'claude', '--agent-home', str(home), '--scope', 'global',
                         '--input', str(self.write_input(root, data)))
            self.assertEqual(json.loads((ledger / 'incidents.jsonl').read_text().splitlines()[-1])['recurrence_of'], 'GLO-4')

    def test_explicit_recurrence_cannot_reference_unknown_or_other_pattern(self):
        for predecessor in ('missing', 'GLO-1'):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                ledger = root / 'reflections'
                ledger.mkdir()
                before = json.dumps(dict(id='GLO-1', pattern_key='other-pattern', level='L3')) + '\n'
                (ledger / 'incidents.jsonl').write_text(before)
                data = incident()
                data['recurrence_of'] = predecessor
                with self.assertRaises(subprocess.CalledProcessError):
                    self.run_cli('record', '--agent-home', str(root), '--scope', 'global',
                                 '--input', str(self.write_input(root, data)))
                self.assertEqual((ledger / 'incidents.jsonl').read_text(), before)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def write_input(self, root: Path, data: dict[str, str]) -> Path:
        path = root / "incident.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_claude_global_uses_its_own_ledger_and_rules_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / ".claude"
            home.mkdir()
            rules = "# Budget: 3 lines.\nShared rules\n"
            (home / "CLAUDE.md").write_text(rules)
            result = self.run_cli("record", "--agent", "claude", "--agent-home", str(home),
                "--scope", "global", "--input", str(self.write_input(root, incident())))
            self.assertTrue((home / "reflections" / "incidents.jsonl").is_file())
            saved = json.loads((home / "reflections" / "incidents.jsonl").read_text())
            self.assertEqual(saved['agent'], 'claude')
            self.assertEqual((home / "CLAUDE.md").read_text(), rules)
            self.assertIn(str(home / "CLAUDE.md"), result.stdout)
            self.assertFalse((root / ".codex").exists())

    def test_claude_project_uses_claude_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.run_cli("record", "--agent", "claude", "--scope", "project",
                "--project-root", str(root), "--input", str(self.write_input(root, incident())))
            self.assertTrue((root / "CLAUDE.md").is_file())
            self.assertNotIn('Whenever Codex', (root / "CLAUDE.md").read_text())
            self.assertNotIn('`AGENTS.md`', (root / "CLAUDE.md").read_text())
            self.assertTrue((root / ".claude" / "reflections" / "incidents.jsonl").is_file())
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertFalse((root / ".codex").exists())

    def test_recurrence_preserves_history_without_automatic_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / ".codex"
            skills = root / ".agents" / "skills"
            self.run_cli("install", "--codex-home", str(home), "--skills-root", str(skills))
            self.assertTrue((skills / "reflect").is_symlink())
            self.assertFalse((home / "AGENTS.md").exists())

            input_path = self.write_input(root, incident())
            for expected_id, expected_level, expected_marker in (
                ("GLO-1", "L1", "**Recurrence:** 1"),
                ("GLO-2", "L2", "**Recurrence:** 2"),
                ("GLO-3", "L3", "**Recurrence:** 3"),
                ("GLO-4", "L4", "**Recurrence:** 4"),
            ):
                result = self.run_cli(
                    "record",
                    "--scope",
                    "global",
                    "--codex-home",
                    str(home),
                    "--input",
                    str(input_path),
                )
                self.assertIn(f"RECORDED: {expected_id}", result.stdout)
                # WHY: the global rules file is lean and shared; the full rule lives in the log only.
                self.assertFalse((home / "AGENTS.md").exists())
                history = (home / "reflections" / "reflection-log.md").read_text(encoding="utf-8")
                self.assertIn(expected_marker, history)

            incidents = [
                json.loads(line)
                for line in (home / "reflections" / "incidents.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([item["level"] for item in incidents], ["L1", "L2", "L3", "L4"])
            self.assertEqual(incidents[1]["recurrence_of"], "GLO-1")
            history = (home / "reflections" / "reflection-log.md").read_text(encoding="utf-8")
            self.assertEqual(history.count("reflect-pattern: instruction-source-confusion"), 4)
            self.assertNotIn("GATE Do not continue", history)
            self.assertNotIn("HALT Do not continue", history)

    def test_global_record_leaves_rules_file_alone_and_reports_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / ".codex"
            home.mkdir()
            rules = "# Shared rules\n# Budget: 4 lines.\n- one\n- two\n"
            (home / "AGENTS.md").write_text(rules, encoding="utf-8")
            input_path = self.write_input(root, incident("budget-pattern"))
            args = ("record", "--scope", "global", "--codex-home", str(home), "--input", str(input_path))

            result = self.run_cli(*args)
            self.assertIn("AGENTS_LINES: 4/4", result.stdout)
            self.assertIn("LINE_BUDGET: OK", result.stdout)
            self.assertEqual((home / "AGENTS.md").read_text(encoding="utf-8"), rules)

            (home / "AGENTS.md").write_text(rules + "- three\n", encoding="utf-8")
            result = self.run_cli(*args)
            self.assertIn("AGENTS_LINES: 5/4", result.stdout)
            self.assertIn("LINE_BUDGET: EXCEEDED", result.stdout)
            self.assertEqual((home / "AGENTS.md").read_text(encoding="utf-8"), rules + "- three\n")

    def test_unreachable_linked_ledger_is_refused(self) -> None:
        # WHY: the ledger folder may be a link into a shared tree; when that tree is
        # unreachable, recording must fail loudly instead of starting a second local log.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / ".codex"
            home.mkdir()
            target = root / "unmounted" / "reflections"
            (home / "reflections").symlink_to(target)
            input_path = self.write_input(root, incident("unreachable-ledger"))

            with self.assertRaises(subprocess.CalledProcessError):
                self.run_cli("record", "--scope", "global", "--codex-home", str(home), "--input", str(input_path))

            self.assertTrue((home / "reflections").is_symlink())
            self.assertFalse(target.parent.exists())

    def test_dry_run_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / ".codex"
            input_path = self.write_input(root, incident("dry-run-pattern"))
            result = self.run_cli(
                "record",
                "--scope",
                "global",
                "--codex-home",
                str(home),
                "--input",
                str(input_path),
                "--dry-run",
            )
            self.assertIn("DRY RUN: GLO-1 L1", result.stdout)
            self.assertFalse(home.exists())

    def test_project_scope_updates_project_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sample-project"
            root.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "master", str(root)], check=True)
            input_path = self.write_input(root, incident("project-only-pattern"))
            result = self.run_cli(
                "record",
                "--scope",
                "project",
                "--project-root",
                str(root),
                "--input",
                str(input_path),
            )
            self.assertIn("RECORDED: SAMP-master-1", result.stdout)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / ".codex" / "reflections" / "incidents.jsonl").exists())

    def test_write_failure_rolls_back_prior_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("original\n", encoding="utf-8")
            real_atomic_write = REFLECTION.atomic_write

            def fail_on_second(path: Path, content: str) -> None:
                if path == second:
                    raise OSError("synthetic write failure")
                real_atomic_write(path, content)

            with mock.patch.object(REFLECTION, "atomic_write", side_effect=fail_on_second):
                with self.assertRaisesRegex(OSError, "synthetic write failure"):
                    REFLECTION.commit_updates({first: "changed\n", second: "new\n"})

            self.assertEqual(first.read_text(encoding="utf-8"), "original\n")
            self.assertFalse(second.exists())

    def test_atomic_write_keeps_symlinked_agents_file(self) -> None:
        # WHY: a global AGENTS.md may be a symlink into a shared tree; replacing the link
        # itself would silently fork this machine's rules from the shared copy.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shared = root / "shared" / "AGENTS.md"
            shared.parent.mkdir()
            shared.write_text("original\n", encoding="utf-8")
            link = root / "AGENTS.md"
            link.symlink_to(shared)

            REFLECTION.atomic_write(link, "changed\n")

            self.assertTrue(link.is_symlink())
            self.assertEqual(shared.read_text(encoding="utf-8"), "changed\n")

    def test_dangling_symlink_is_refused_and_kept(self) -> None:
        # WHY: a dangling AGENTS.md link means the shared tree is unreachable (share not
        # mounted); writing would recreate its path locally or drop the link on rollback.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "unmounted" / "AGENTS.md"
            link = root / "AGENTS.md"
            link.symlink_to(target)

            with self.assertRaisesRegex(OSError, "dangling symlink"):
                REFLECTION.commit_updates({link: "changed\n"})

            self.assertTrue(link.is_symlink())
            self.assertFalse(target.parent.exists())


if __name__ == "__main__":
    unittest.main()
