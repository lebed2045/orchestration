#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
import subprocess
import tempfile
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

    def test_install_and_escalation_ladder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / ".codex"
            skills = root / ".agents" / "skills"
            self.run_cli("install", "--codex-home", str(home), "--skills-root", str(skills))
            self.assertTrue((skills / "reflect").is_symlink())
            self.assertFalse((home / "AGENTS.md").exists())

            input_path = self.write_input(root, incident())
            for expected_id, expected_level, expected_marker in (
                ("GLO-1", "L1", "L1 REMINDER"),
                ("GLO-2", "L2", "L2 MANDATORY PROOF"),
                ("GLO-3", "L3", "L3 HARD GATE"),
                ("GLO-4", "L4", "L4 HALT"),
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
            self.assertIn("GATE Do not continue", history)
            self.assertIn("HALT Do not continue", history)

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
            subprocess.run(["git", "init", "-q", str(root)], check=True)
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
