"""Exercise real CLI review/apply effects using isolated shared-root fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import importlib.util
import shutil

SCRIPT = Path(__file__).with_name('reflection.py')


class GlobalReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rules = self.root / 'global/AGENTS.md'
        self.rules.parent.mkdir()
        self.before = '# Global rules\n# Budget: 150 lines.\n- Preserve existing rules.\n'
        self.rules.write_text(self.before)
        self.rules.chmod(0o644)
        self.output = self.root / 'review.json'
        for source in ('host-codex','host-claude','vm-codex','vm-claude'):
            self.add_incident(source)

    def add_incident(self, source, rule='- Check evidence before reporting success.', pattern='evidence-gap', ident='GLO-1', **extra):
        folder = self.root / f'global/inbox/{source}/reflections'
        folder.mkdir(parents=True, exist_ok=True)
        row = dict(id=ident, pattern_key=pattern, what='Reported success without evidence.',
                   root_cause='Skipped a live check.', proposed_global_rule=rule,
                   evidence=['A failed check.'], **extra)
        with (folder / 'incidents.jsonl').open('a') as handle:
            handle.write(json.dumps(row)+'\n')

    def run_cli(self, command, *args, ok=True):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), command, '--root', str(self.root), *args],
                                text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
        return result

    def review(self, *extra):
        result = self.run_cli('review', '--output', str(self.output), *extra)
        return json.loads(result.stdout)

    def apply(self, *extra, ok=True):
        return self.run_cli('apply', '--review', str(self.output), '--confirm', *extra, ok=ok)

    def test_renew_without_confirm_changes_nothing(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        result = json.loads(self.run_cli('renew', '--date', '2026-11-05').stdout)
        self.assertFalse(result['renewed'])
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))

    def test_renew_archives_rules_and_inbox_and_leaves_empty_inboxes(self):
        result = json.loads(self.run_cli('renew', '--date', '2026-11-05', '--confirm').stdout)
        self.assertTrue(result['renewed'])
        dest = self.root / 'global/archive/2026-11-05'
        self.assertEqual((dest / 'AGENTS.md').read_text(), self.before)
        self.assertEqual(self.rules.read_text(), self.before)
        for role in ('host-codex','host-claude','vm-codex','vm-claude'):
            self.assertIn('GLO-1', (dest / f'inbox/{role}/reflections/incidents.jsonl').read_text())
            live = self.root / f'global/inbox/{role}/reflections'
            self.assertTrue(live.is_dir())
            self.assertEqual(list(live.iterdir()), [])
        review = json.loads(self.run_cli('review').stdout)
        self.assertTrue(all(review['coverage'][r]['state'] != 'recorded' for r in review['coverage']))

    def test_renew_never_reuses_an_archive_folder(self):
        (self.root / 'global/archive/2026-11-05').mkdir(parents=True)
        result = self.run_cli('renew', '--date', '2026-11-05', '--confirm', ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / 'global/inbox/vm-codex/reflections/incidents.jsonl').exists())

    # Writing during default review would fail the unchanged-tree assertion.
    def test_review_reads_all_four_roles_deduplicates_and_writes_nothing(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        result = json.loads(self.run_cli('review').stdout)
        self.assertEqual(set(result['coverage']), {'host-codex','host-claude','vm-codex','vm-claude'})
        self.assertTrue(all(result['coverage'][r]['state'] == 'recorded' for r in result['coverage']))
        self.assertEqual(len(result['edits']), 1)
        self.assertEqual(len(result['edits'][0]['sources']), 4)
        self.assertIn('+- Check evidence before reporting success.', result['diff'])
        self.assertEqual(self.rules.read_text(), self.before)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))

    def test_only_explicit_apply_changes_rules_and_preserves_recovery_copy(self):
        self.review()
        refused = self.run_cli('apply', '--review', str(self.output), ok=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(self.rules.read_text(), self.before)
        result = json.loads(self.apply().stdout)
        self.assertEqual(self.rules.read_text(), self.before+'- Check evidence before reporting success.\n')
        self.assertEqual(Path(result['backup']).read_text(), self.before)
        self.assertEqual(json.loads(Path(result['receipt']).read_text())['status'], 'applied')
        self.assertEqual(self.rules.stat().st_mode & 0o777, 0o644)
        second = self.apply(ok=False)
        self.assertNotEqual(second.returncode, 0)

    def test_stale_or_tampered_review_never_changes_rules(self):
        self.review()
        self.rules.write_text(self.before+'- Another agent changed this.\n')
        current = self.rules.read_text()
        self.assertNotEqual(self.apply(ok=False).returncode, 0)
        self.assertEqual(self.rules.read_text(), current)
        self.rules.write_text(self.before)
        plan = json.loads(self.output.read_text())
        plan['edits'][0]['new'] = '- An unreviewed edit.'
        self.output.write_text(json.dumps(plan))
        self.assertNotEqual(self.apply(ok=False).returncode, 0)
        self.assertEqual(self.rules.read_text(), self.before)

    def test_conflicting_proposals_need_explicit_selection(self):
        self.add_incident('vm-codex', rule='- A conflicting alternative.', ident='GLO-2')
        data = self.review()
        self.assertFalse(data['ready_to_apply'])
        self.assertTrue(data['conflicts'])
        self.assertNotEqual(self.apply(ok=False).returncode, 0)
        selected = json.loads(self.run_cli('review', '--select', 'host-codex:GLO-1').stdout)
        self.assertTrue(selected['ready_to_apply'])
        self.assertEqual(len(selected['edits']), 1)

    def test_missing_roles_and_legacy_rows_are_reported_without_fabricating_rules(self):
        extra = self.root / 'global/inbox/host-old-codex/reflections'
        extra.mkdir(parents=True)
        (extra/'incidents.jsonl').write_text(json.dumps({'id':'OLD-1','root_cause':'Legacy cause','level':'L3'})+'\n')
        # A new empty fixture contains no agent logs at all.
        absent = self.root / 'empty'
        (absent/'global').mkdir(parents=True)
        (absent/'global/AGENTS.md').write_text(self.before)
        result = subprocess.run([sys.executable, '-B', str(SCRIPT),'review','--root',str(absent)],capture_output=True,text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(v['state']=='missing' for v in json.loads(result.stdout)['coverage'].values()))
        data = json.loads(self.run_cli('review').stdout)
        self.assertIn('host-old-codex:OLD-1', data['needs_proposal'])
        self.assertNotIn('Legacy cause', '\n'.join(x['new'] for x in data['edits']))

    def test_named_output_never_overwrites_or_escapes_the_shared_root(self):
        self.output.write_text('user file')
        self.assertNotEqual(self.run_cli('review','--output',str(self.output),ok=False).returncode, 0)
        self.assertEqual(self.output.read_text(), 'user file')
        self.assertNotEqual(self.run_cli('review','--output',str(self.root.parent/'escape.json'),ok=False).returncode, 0)

    def test_budget_and_unknown_selection_refuse_before_writing(self):
        self.rules.write_text('# Budget: 2 lines.\n- Existing.\n')
        data = self.review()
        self.assertFalse(data['ready_to_apply'])
        self.assertNotEqual(self.apply(ok=False).returncode, 0)
        self.assertEqual(self.rules.read_text(), '# Budget: 2 lines.\n- Existing.\n')
        self.assertNotEqual(self.run_cli('review','--select','missing:ID',ok=False).returncode, 0)

    def test_explicit_replacement_preserves_unrelated_lines(self):
        # An independent pattern with an explicit old line produces a reviewed replacement.
        self.add_incident('host-codex', rule='- Preserve unrelated rules exactly.', pattern='preservation', ident='GLO-2',
                          replaces_global_rule='- Preserve existing rules.')
        self.review('--select','host-codex:GLO-2')
        self.apply()
        self.assertEqual(self.rules.read_text(), '# Global rules\n# Budget: 150 lines.\n- Preserve unrelated rules exactly.\n')

    def test_redirected_home_cache_and_temp_receive_no_unrequested_outputs(self):
        sandbox = self.root / 'redirects'
        sandbox.mkdir()
        env = dict(os.environ, HOME=str(sandbox), TMPDIR=str(sandbox), XDG_CACHE_HOME=str(sandbox), PYTHONDONTWRITEBYTECODE='1')
        command = [sys.executable,'-B',str(SCRIPT),'review','--root',str(self.root),'--output',str(self.output)]
        result = subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable,'-B',str(SCRIPT),'apply','--root',str(self.root),'--review',str(self.output),'--confirm'],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(sandbox.iterdir()), [])
        self.assertEqual(list(self.root.glob('.reflect-*')), [])

    def test_dangling_log_source_is_reported_as_unreadable(self):
        folder = self.root / 'global/inbox/vm-other-codex'
        folder.mkdir()
        (folder/'reflections').symlink_to(self.root/'missing-share')
        data = json.loads(self.run_cli('review').stdout)
        self.assertTrue(data['source_errors'])
        self.assertFalse(data['ready_to_apply'])

    def test_duplicate_legacy_ids_keep_both_rows_with_unambiguous_source_tokens(self):
        self.add_incident('vm-claude', ident='GLO-1', rule=None, pattern='old-pattern')
        data = json.loads(self.run_cli('review').stdout)
        self.assertFalse(data['source_errors'])
        self.assertTrue(data['source_warnings'])
        self.assertIn('vm-claude:GLO-1@2', data['needs_proposal'])
        selected = {token for edit in data['edits'] for token in edit['sources']}
        self.assertIn('vm-claude:GLO-1@1', selected)
        self.assertEqual(data['coverage']['vm-claude']['state'], 'recorded')

    def test_manual_review_can_synthesize_a_rule_from_legacy_evidence(self):
        legacy = self.root / 'global/inbox/host-old-codex/reflections'
        legacy.mkdir(parents=True)
        (legacy/'incidents.jsonl').write_text(json.dumps({'id':'OLD-1','root_cause':'Same missing evidence.'})+'\n')
        proposal = self.root / 'proposal.json'
        proposal.write_text(json.dumps({'edits':[{'old':None, 'new':'- Show current evidence before success claims.',
                                                 'sources':['host-old-codex:OLD-1','host-codex:GLO-1']}]}))
        self.review('--proposal',str(proposal))
        self.apply()
        self.assertIn('- Show current evidence before success claims.', self.rules.read_text())
        self.assertNotIn('- Check evidence before reporting success.', self.rules.read_text())

    def test_apply_receipt_failure_restores_original_rules_and_reports_rollback(self):
        self.review()
        spec = importlib.util.spec_from_file_location('global_review_failure_test', SCRIPT.with_name('global_review.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        def writer(path, text):
            if path.name == 'receipt.json' and json.loads(text)['status'] == 'applied':
                raise OSError('injected receipt write failure')
            path.write_text(text)
        with self.assertRaises(OSError):
            module.apply_review(self.root, str(self.output), True, writer)
        self.assertEqual(self.rules.read_text(), self.before)
        receipts = list((self.root/'global/archive/applied').glob('*/receipt.json'))
        self.assertEqual(json.loads(receipts[0].read_text())['status'], 'rolled_back')

    def test_apply_never_overwrites_an_intervening_user_edit(self):
        self.review()
        spec = importlib.util.spec_from_file_location('global_review_race_test', SCRIPT.with_name('global_review.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        other = self.before+'- A simultaneous user edit.\n'
        def writer(path, text):
            path.write_text(text)
            if path.name == 'receipt.json' and json.loads(text)['status'] == 'prepared':
                self.rules.write_text(other)
        with self.assertRaises(ValueError):
            module.apply_review(self.root, str(self.output), True, writer)
        self.assertEqual(self.rules.read_text(), other)

    def test_apply_rechecks_incident_evidence_after_preparation(self):
        self.review()
        spec = importlib.util.spec_from_file_location('global_review_evidence_race', SCRIPT.with_name('global_review.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        def writer(path, text):
            path.write_text(text)
            if path.name == 'receipt.json' and json.loads(text)['status'] == 'prepared':
                source = self.root/'global/inbox/host-codex/reflections/incidents.jsonl'
                source.write_text(source.read_text().replace('Skipped a live check.', 'The evidence was corrected.'))
        with self.assertRaises(ValueError):
            module.apply_review(self.root, str(self.output), True, writer)
        self.assertEqual(self.rules.read_text(), self.before)

    def test_documented_python_invocation_leaves_no_bytecode_or_home_outputs(self):
        runner = self.root / 'runner'
        runner.mkdir()
        for filename in ('reflection.py','global_review.py'):
            shutil.copy2(SCRIPT.with_name(filename), runner/filename)
        redirected = self.root / 'redirected'
        redirected.mkdir()
        env = dict(os.environ, HOME=str(redirected), TMPDIR=str(redirected), XDG_CACHE_HOME=str(redirected))
        env.pop('PYTHONDONTWRITEBYTECODE', None)
        result = subprocess.run([sys.executable,'-B',str(runner/'reflection.py'),'review','--root',str(self.root)],
                                env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(p.name for p in runner.iterdir()), ['global_review.py','reflection.py'])
        self.assertEqual(list(redirected.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
