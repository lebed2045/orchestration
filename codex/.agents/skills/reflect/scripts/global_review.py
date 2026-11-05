"""Explicit, offline promotion of shared reflection proposals. Updated 27-oct-2026."""
from __future__ import annotations

import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime, timezone
import uuid
from collections import Counter

LIMIT = 8 * 1024 * 1024
ROLES = ('host-codex', 'host-claude', 'vm-codex', 'vm-claude')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def contained(root, path):
    path = Path(path).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'Path escapes shared checkout: {path}')
    return path


def read_file(path):
    if path.stat().st_size > LIMIT:
        raise ValueError(f'File exceeds 8 MiB: {path}')
    return path.read_text(encoding='utf-8')


def global_target(root):
    path = contained(root, root / 'global/AGENTS.md')
    if not path.is_file():
        raise ValueError(f'Global rules file is unavailable: {path}')
    return path


def rows_from(path):
    rows = []
    for number, line in enumerate(read_file(path).splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise ValueError(f'Invalid incident ID: {path}:{number}')
        rows.append((number, row))
    return rows


def scan(root):
    coverage = {role: {'state': 'missing', 'sources': []} for role in ROLES}
    records, errors, warnings = {}, [], []
    log = contained(root, root / 'global/inbox')
    if not log.exists():
        return coverage, records, errors, warnings
    folders = sorted(log.iterdir())
    if len(folders) > 1000:
        raise ValueError('More than 1000 log entries; narrow the registry before reviewing')
    for folder in folders:
        if not folder.is_dir():
            if folder.is_symlink():
                errors.append(f'Unreachable log folder: {folder.name}')
            continue
        ledger = folder / 'reflections'
        if not ledger.exists() and not ledger.is_symlink():
            continue
        role = next((r for r in ROLES if folder.name == r or
                     (folder.name.startswith(r.split('-')[0]+'-') and folder.name.endswith('-'+r.split('-')[1]))), None)
        relative = str((ledger / 'incidents.jsonl').relative_to(root))
        try:
            contained(root, ledger)
            if not ledger.is_dir():
                raise ValueError(f'Unreachable ledger: {ledger}')
            path = contained(root, ledger / 'incidents.jsonl')
            entries = rows_from(path) if path.exists() or path.is_symlink() else []
            if role:
                coverage[role]['sources'].append(relative)
                if entries:
                    coverage[role]['state'] = 'recorded'
                elif coverage[role]['state'] == 'missing':
                    coverage[role]['state'] = 'empty'
            counts = Counter(row['id'] for _, row in entries)
            for number, row in entries:
                suffix = f'@{number}' if counts[row['id']] > 1 else ''
                token = f'{folder.name}:{row["id"]}{suffix}'
                if suffix:
                    warnings.append(f'Duplicate legacy ID retained as {token}')
                if token in records:
                    raise ValueError(f'Ambiguous incident token: {token}')
                records[token] = {'source': relative, 'id': row['id'], 'row': row,
                                  'sha256': digest(json.dumps(row, sort_keys=True, ensure_ascii=False))}
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f'{relative}: {exc}')
            if role:
                coverage[role]['state'] = 'unreadable'
    return coverage, records, errors, warnings


def bullet(value):
    if not isinstance(value, str) or not value.startswith('- ') or len(value.splitlines()) != 1 or len(value) > 2000:
        raise ValueError('A global rule must be one Markdown bullet, at most 2000 characters')
    return value


def edit_text(before, edits):
    lines = before.splitlines()
    touched = set()
    for edit in edits:
        new = bullet(edit['new'])
        old = edit.get('old')
        if old is not None:
            bullet(old)
            if old in touched or lines.count(old) != 1:
                raise ValueError('Replacement must name one untouched existing rule')
            touched.add(old)
            lines[lines.index(old)] = new
        elif new not in lines:
            lines.append(new)
    return '\n'.join(lines)+'\n' if edits else before


def patch(before, after):
    return ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                      fromfile='global/AGENTS.md', tofile='global/AGENTS.md'))


def budget_ok(text):
    match = re.search(r'^# Budget: (\d+) lines', text, re.M)
    return len(text.splitlines()) <= (int(match.group(1)) if match else 150)


def review(root, selected, proposal=None):
    target = global_target(root)
    before = read_file(target)
    coverage, records, errors, warnings = scan(root)
    if set(selected) - records.keys():
        raise ValueError(f'Unknown incident selection: {sorted(set(selected)-records.keys())}')
    chosen = {key: records[key] for key in selected} if selected else records
    groups, needs, conflicts = {}, [], []
    for token, item in chosen.items():
        row = item['row']
        if not row.get('proposed_global_rule'):
            needs.append(token)
            continue
        key = row.get('pattern_key') or token
        candidate = (bullet(row['proposed_global_rule']), row.get('replaces_global_rule'))
        if candidate[1] is not None:
            bullet(candidate[1])
        groups.setdefault(key, {}).setdefault(candidate, []).append(token)
    edits_by_rule = {}
    for key, alternatives in groups.items():
        if len(alternatives) != 1:
            conflicts.append({'pattern_key': key, 'alternatives': [dict(new=p[0], old=p[1], sources=tokens)
                                                                 for p, tokens in alternatives.items()]})
            continue
        candidate, tokens = next(iter(alternatives.items()))
        edits_by_rule.setdefault(candidate, []).extend(tokens)
    edits = [{'old': old, 'new': new, 'sources': tokens} for (new, old), tokens in edits_by_rule.items()
             if old is not None or new not in before.splitlines()]
    if proposal:
        document = json.loads(read_file(contained(root, proposal)))
        edits = document['edits']
        if not isinstance(edits, list):
            raise ValueError('Proposal edits must be a list')
        for edit in edits:
            if not isinstance(edit, dict) or not isinstance(edit.get('sources'), list) or not edit['sources']:
                raise ValueError('Each proposed edit needs incident sources')
            if any(token not in chosen for token in edit['sources']):
                raise ValueError('Proposed edit references an unknown/unselected incident')
        # A human-requested synthesis resolves the alternatives; provenance stays attached.
        conflicts = []
    try:
        after = edit_text(before, edits)
    except ValueError as exc:
        errors.append(str(exc))
        after = before
    if not budget_ok(after):
        errors.append('Proposed global rules exceed their line budget; merge/replace a rule instead')
    used = {token for edit in edits for token in edit['sources']}
    return {'schema_version': 1, 'kind': 'reflection-global-review',
            'target': 'global/AGENTS.md', 'resolved_target': str(target.resolve().relative_to(root)),
            'base_sha256': digest(before), 'after_sha256': digest(after),
            'proposal_origin': 'reviewed-synthesis' if proposal else 'recorded-proposals',
            'coverage': coverage, 'source_errors': errors, 'source_warnings': warnings, 'needs_proposal': needs,
            'conflicts': conflicts, 'edits': edits,
            'evidence': {token: {k: v for k, v in records[token].items() if k != 'row'} for token in sorted(used)},
            'diff': patch(before, after),
            'ready_to_apply': bool(edits) and not errors and not conflicts,
            'runtime_state': 'Shared log evidence only; live VM sessions are untested'}


def new_output(root, value, text):
    output = contained(root, value)
    if not output.parent.is_dir():
        raise ValueError('Output parent must already exist')
    # An atomic, exclusive publish preserves user files even if one appears during review.
    with tempfile.TemporaryDirectory(prefix='.reflect-review-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'review.json'
        staged.write_text(text, encoding='utf-8')
        os.link(staged, output)
    return output


def validate_evidence(root, plan):
    _, current, errors, _ = scan(root)
    if errors:
        raise ValueError('Some log sources are unreadable; review again')
    for edit in plan['edits']:
        if not edit.get('sources'):
            raise ValueError('Each global edit needs a recorded proposal')
        for token in edit['sources']:
            if token not in current or current[token]['sha256'] != plan.get('evidence', {}).get(token, {}).get('sha256'):
                raise ValueError(f'Incident changed since review: {token}')
            row = current[token]['row']
            if plan.get('proposal_origin') != 'reviewed-synthesis' and (row.get('proposed_global_rule') != edit['new'] or row.get('replaces_global_rule') != edit.get('old')):
                raise ValueError('Edit does not match the selected recorded proposal')


def apply_review(root, value, confirm, writer):
    if not confirm:
        raise ValueError('Global apply requires explicit --confirm after the user approves the displayed diff')
    plan = json.loads(read_file(contained(root, value)))
    if plan.get('schema_version') != 1 or plan.get('kind') != 'reflection-global-review' or plan.get('target') != 'global/AGENTS.md':
        raise ValueError('Not a global reflection review')
    if plan.get('ready_to_apply') is not True or plan.get('source_errors') or plan.get('conflicts') or not plan.get('edits'):
        raise ValueError('Review has unresolved errors/conflicts or no selected changes')
    target = global_target(root)
    state = contained(root, root / 'global/archive/applied')
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'apply.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = read_file(target)
        if str(target.resolve().relative_to(root)) != plan.get('resolved_target') or digest(before) != plan.get('base_sha256'):
            raise ValueError('Global rules changed since review; review again before applying')
        after = edit_text(before, plan['edits'])
        if digest(after) != plan.get('after_sha256') or patch(before, after) != plan.get('diff') or not budget_ok(after):
            raise ValueError('Reviewed diff/hash/line budget does not match the requested edit')
        validate_evidence(root, plan)
        run = state / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
        run.mkdir()
        backup, receipt = run / 'before.md', run / 'receipt.json'
        new_output(root, backup, before)
        data = {'schema_version': 1, 'status': 'prepared', 'review_sha256': digest(json.dumps(plan, sort_keys=True)),
                'base_sha256': digest(before), 'after_sha256': digest(after), 'target': str(target),
                'backup': str(backup), 'sources': sorted(plan['evidence'])}
        writer(receipt, json.dumps(data, indent=2)+'\n')
        try:
            validate_evidence(root, plan)
            if read_file(target) != before or str(target.resolve().relative_to(root)) != plan['resolved_target']:
                raise ValueError('Global rules changed while preparing apply; the new edit was preserved')
            writer(target, after)
            data['status'] = 'applied'
            writer(receipt, json.dumps(data, indent=2)+'\n')
        except BaseException as exc:
            current_text = read_file(target)
            if current_text == after:
                writer(target, before)
            data['status'] = 'rolled_back' if current_text in (before, after) else 'recovery_required'
            data['error'] = str(exc)
            writer(receipt, json.dumps(data, indent=2)+'\n')
            raise
    return {'status': 'applied', 'target': str(target), 'backup': str(backup), 'receipt': str(receipt),
            'runtime_discovery': 'Updated instructions take effect when the consuming agent reloads them; untested'}


def renew(root, date, confirm):
    """Archive the current rules and every inbox file into archive/<date>; leave empty inboxes."""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date or ''):
        raise ValueError('--date must be YYYY-MM-DD')
    rules = global_target(root)
    inbox = contained(root, root / 'global/inbox')
    dest = contained(root, root / 'global/archive' / date)
    if dest.exists() or dest.is_symlink():
        raise ValueError(f'Archive folder already exists; pick another date label: {dest}')
    moves = []
    for ledger in sorted(inbox.glob('*/reflections')) if inbox.is_dir() else []:
        for item in sorted(ledger.iterdir()):
            moves.append((item, dest / item.relative_to(root / 'global')))
    plan = {'renewed': False, 'archive': str(dest.relative_to(root)), 'rules_snapshot': 'AGENTS.md',
            'moves': [str(src.relative_to(root)) for src, _ in moves]}
    if not confirm:
        return plan
    dest.mkdir(parents=True)
    (dest / 'AGENTS.md').write_text(read_file(rules), encoding='utf-8')
    for src, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, target)
    plan['renewed'] = True
    return plan


def add_commands(subparsers, writer, default_root):
    def handle_review(args):
        root = Path(args.root).expanduser().resolve()
        result = review(root, args.select, args.proposal)
        text = json.dumps(result, indent=2, ensure_ascii=False)+'\n'
        if args.output:
            new_output(root, args.output, text)
        print(text, end='')
        return 0

    def handle_apply(args):
        result = apply_review(Path(args.root).expanduser().resolve(), args.review, args.confirm, writer)
        print(json.dumps(result, indent=2))
        return 0

    def handle_renew(args):
        result = renew(Path(args.root).expanduser().resolve(), args.date, args.confirm)
        print(json.dumps(result, indent=2))
        return 0

    command = subparsers.add_parser('review', help='read all shared reflection logs and propose a global diff')
    command.add_argument('--root', default=str(default_root))
    command.add_argument('--select', action='append', default=[], help='exact source-folder:incident-ID; repeat to select proposals')
    command.add_argument('--output', help='new named review JSON under the shared checkout; otherwise print only')
    command.add_argument('--proposal', help='explicit synthesized edits JSON with incident source IDs')
    command.set_defaults(func=handle_review)
    command = subparsers.add_parser('apply', help='apply an explicitly approved global reflection review')
    command.add_argument('--root', default=str(default_root))
    command.add_argument('--review', required=True)
    command.add_argument('--confirm', action='store_true')
    command.set_defaults(func=handle_apply)
    command = subparsers.add_parser('renew', help='after an applied review: archive rules + inbox to global/archive/<date>, empty the inbox')
    command.add_argument('--root', default=str(default_root))
    command.add_argument('--date', required=True, help='archive folder label, YYYY-MM-DD')
    command.add_argument('--confirm', action='store_true', help='without it, only print what would move')
    command.set_defaults(func=handle_renew)
