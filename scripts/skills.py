#!/usr/bin/env python3
"""Preview, register and restore selected shared skills. Updated 15-oct-2026; stdlib only."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid


class SetupError(Exception):
    pass


def exists(path):
    return os.path.lexists(path)


def read_json(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise SetupError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SetupError(f"Unsupported schema in {path}")
    return value


def inside(base, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise SetupError(f"Unsafe relative path: {relative}")
    return base / path


def check_parents(path, base):
    for parent in path.parents:
        if parent == base:
            break
        if parent.is_symlink():
            raise SetupError(f"Symlink parent would redirect registration: {parent}")
        if exists(parent) and not parent.is_dir():
            raise SetupError(f"Parent is not a directory: {parent}")


def target_path(home, relative):
    path = inside(home, relative)
    prefixes = ((".agents", "skills"), (".codex", "skills"),
                (".claude", "skills"), (".claude", "commands"))
    ledger = Path(relative).parts in ((".codex", "reflections"), (".claude", "reflections"))
    if not ledger and (Path(relative).parts[:2] not in prefixes or len(Path(relative).parts) != 3):
        raise SetupError(f"Target is not one individual skill/command: {relative}")
    check_parents(path, home)
    return path


def definitions(root):
    registry = read_json(root / "skills.json")
    skills = registry.get("skills")
    if not isinstance(skills, dict):
        raise SetupError("skills.json must contain a skills object")
    result = dict(skills)
    dependencies = read_json(root / "dependencies.json").get("dependencies", [])
    for dependency in dependencies:
        for name in dependency.get("available_skills", []):
            key = f'{dependency["name"]}:{name}'
            if key in result:
                raise SetupError(f"Duplicate registry key: {key}")
            source = str(Path(dependency["source_directory"]) / dependency["skills_directory"] / name)
            result[key] = {"provider": dependency["name"], "dependency": dependency,
                "engines": {engine: [{"source": source, "target": f'{prefix}/{name}', "kind": "skill"}]
                    for engine, prefix in (("codex", ".agents/skills"), ("claude", ".claude/skills"))}}
    return result


def potential_plugins(home, provider):
    found = []
    for prefix in (home / ".codex/plugins/cache", home / ".claude/plugins/cache"):
        if prefix.is_dir():
            found.extend(str(p) for p in prefix.glob(f"*/{provider}/*") if p.is_dir())
    return sorted(found)


def link_state(target, source):
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return "linked" if target.exists() else "dangling"
        return "conflict"
    return "conflict" if exists(target) else "missing"


def dependency_integrity(root, dependency):
    directory = inside(root, dependency["source_directory"])
    if not directory.resolve().is_relative_to(root.resolve()):
        return {"status": "unverified", "error": "Dependency source escapes shared checkout"}
    expected = dependency.get("commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        return {"status": "unverified", "error": "Dependency requires an immutable 40-character commit pin"}
    prefix = ["git", "-c", f"safe.directory={directory}", "-c", "core.fsmonitor=false",
              "-c", "core.hooksPath=/dev/null", "-C", str(directory)]
    try:
        head = subprocess.run(prefix + ["rev-parse", "--verify", "HEAD^{commit}"], capture_output=True, text=True, timeout=15)
        if head.returncode or head.stdout.strip() != expected:
            return {"status": "unverified", "error": f"Dependency source revision does not match {expected}"}
        state = subprocess.run(prefix + ["status", "--short"], capture_output=True, text=True, timeout=15)
        if state.returncode or state.stdout.strip():
            return {"status": "unverified", "error": "Dependency source is dirty or unreadable; preserve customizations as reviewed tracked patches"}
        for relative, digest in dependency.get("reference_files_sha256", {}).items():
            file = inside(directory, relative)
            if not file.resolve().is_relative_to(directory.resolve()):
                return {"status": "unverified", "error": "Dependency checksum path escapes source"}
            if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                return {"status": "unverified", "error": f"Dependency checksum mismatch: {relative}"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unverified", "error": str(exc)}
    return {"status": "verified", "commit": expected}


def plan(root, home, engines, selected, machine=None):
    known = definitions(root)
    if not selected:
        raise SetupError("Select at least one --skill; there is no implicit install-all")
    operations, seen, retirement_candidates = [], set(), set()
    checked_dependencies = {}
    for key in dict.fromkeys(selected):
        if key not in known:
            raise SetupError(f"Unknown skill: {key}")
        spec = known[key]
        dependency = spec.get("dependency")
        approved = dependency is None or key.split(":", 1)[1] in dependency.get("selected_skills", [])
        integrity = None
        if dependency and approved:
            provider = spec["provider"]
            if provider not in checked_dependencies:
                checked_dependencies[provider] = dependency_integrity(root, dependency)
            integrity = checked_dependencies[provider]
        for engine in engines:
            entries = list(spec.get("engines", {}).get(engine, []))
            if not entries:
                raise SetupError(f"{key} has no {engine} implementation")
            if spec.get("route_ledgers"):
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", machine or ""):
                    raise SetupError("Reflection routing requires --machine with a unique host/guest label")
                entries.append({"source": f"global/inbox/{machine}-{engine}/reflections",
                                "target": f".{engine}/reflections", "kind": "ledger"})
            for entry in entries:
                target = target_path(home, entry["target"])
                if str(target) in seen:
                    raise SetupError(f"Two selected skills own the same target: {target}")
                seen.add(str(target))
                source = inside(root, entry["source"])
                if not source.resolve().is_relative_to(root):
                    raise SetupError(f"Source escapes shared checkout: {source}")
                marker = source / "SKILL.md" if entry["kind"] == "skill" else source
                if marker.exists() and not marker.resolve().is_relative_to(root):
                    raise SetupError(f"Skill entrypoint escapes shared checkout: {marker}")
                legacy = []
                if engine == "codex" and entry["kind"] == "skill":
                    old = target_path(home, f'.codex/skills/{target.name}')
                    if old != target:
                        retirement_candidates.add(str(old))
                    if old != target and exists(old):
                        legacy.append(str(old))
                for relative in spec.get("legacy_targets", {}).get(engine, []):
                    old = target_path(home, relative)
                    if old != target:
                        retirement_candidates.add(str(old))
                    if old != target and exists(old):
                        legacy.append(str(old))
                operations.append({"skill": key, "engine": engine, "source": str(source), "kind": entry["kind"],
                    "target": str(target), "source_available": marker.is_dir() if entry["kind"] == "ledger" else marker.is_file(),
                    "state": link_state(target, source), "legacy_duplicates": legacy,
                    "dependency_selected": approved, "provider": spec.get("provider", "orchestration"),
                    "source_integrity": integrity,
                    "potential_plugin_caches": potential_plugins(home, spec["provider"]) if dependency else []})
    if seen & retirement_candidates:
        raise SetupError(f"A retirement would remove another selected target: {sorted(seen & retirement_candidates)}")
    return {"root": str(root), "home": str(home), "operations": operations,
            "runtime_discovery": "untested; inspect a fresh agent session"}


def footprint(path):
    """Bound backup work before touching either a local home or a shared mount."""
    count, total = 0, 0
    pending = [path]
    while pending:
        item = pending.pop()
        count += 1
        if count > 1000:
            raise SetupError(f"Backup exceeds 1000 entries; migrate separately: {path}")
        info = item.lstat()
        total += info.st_size
        if total > 8 * 1024 * 1024:
            raise SetupError(f"Backup exceeds 8 MiB; migrate separately: {path}")
        if item.is_dir() and not item.is_symlink():
            pending.extend(item.iterdir())


def preflight(data, replace=False, retire=False, native_disabled=()):
    retired = set()
    for operation in data["operations"]:
        if operation.get("kind") == "ledger":
            source, target = Path(operation["source"]), Path(operation["target"])
            if exists(source) and not source.is_dir():
                raise SetupError(f"Shared ledger is not a directory: {source}")
            if exists(target) and not target.is_dir():
                raise SetupError(f"Existing ledger is not reachable as a directory: {target}")
            if source.is_dir() and target.is_dir() and source.resolve() != target.resolve():
                if directory_digest(source) != directory_digest(target):
                    raise SetupError(f"Divergent reflection history; merge separately before routing: {target}, {source}")
            if target.is_dir() and source.resolve() != target.resolve():
                footprint(target.resolve())
        elif not operation["source_available"]:
            raise SetupError(f'Missing shared source: {operation["source"]}')
        if not operation["dependency_selected"]:
            raise SetupError(f'Dependency skill is not selected in dependencies.json: {operation["skill"]}')
        if operation.get("source_integrity") and operation["source_integrity"]["status"] != "verified":
            raise SetupError(operation["source_integrity"]["error"])
        if operation["state"] == "conflict" and not replace:
            raise SetupError(f'Existing target needs explicit --replace: {operation["target"]}')
        if operation["legacy_duplicates"] and not retire:
            raise SetupError(f'Legacy duplicate needs explicit --retire-legacy: {operation["legacy_duplicates"]}')
        if operation["potential_plugin_caches"] and operation["provider"] not in native_disabled:
            raise SetupError(f'Native package cache present for {operation["provider"]}; its active state cannot be inferred from cache. Confirm native deactivation separately, then use --native-disabled {operation["provider"]}.')
        if operation["state"] == "conflict":
            footprint(Path(operation["target"]))
        for value in operation["legacy_duplicates"]:
            if value not in retired:
                footprint(Path(value))
                retired.add(value)


def state_directory(root):
    result = root / "global" / "registrations"
    check_parents(result / "probe", root)
    return result


@contextmanager
def mutation_lock(root, home):
    state = state_directory(root)
    state.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(home).encode()).hexdigest()[:20]
    lock = state / f"{key}.lock"
    with lock.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SetupError("Another registration/restore is active for this home") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def save_receipt(path, receipt):
    temporary = path.with_name(f"receipt-{uuid.uuid4().hex}.pending")
    with temporary.open("x") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def backup_move(target, backup):
    if exists(backup):
        raise SetupError(f"Backup already exists: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(target), str(backup))


def directory_digest(path):
    path = path.resolve()
    footprint(path)
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        digest.update(str(item.relative_to(path)).encode() + b"\0")
        if item.is_symlink():
            digest.update(b"link\0" + os.readlink(item).encode())
        elif item.is_file():
            digest.update(b"file\0" + item.read_bytes())
        elif item.is_dir():
            digest.update(b"dir\0")
        else:
            raise SetupError(f"Unsupported ledger entry: {item}")
    return digest.hexdigest()


def prepare_ledger(operation):
    if operation.get("kind") != "ledger":
        return
    source, target = Path(operation["source"]), Path(operation["target"])
    if not exists(source):
        source.parent.mkdir(parents=True, exist_ok=True)
        if target.is_dir():
            shutil.copytree(target.resolve(), source, symlinks=True)
            if directory_digest(source) != directory_digest(target):
                raise SetupError(f"Reflection history changed during copy; original retained: {target}")
        else:
            source.mkdir()


def undo_items(items, folder, checkpoint):
    """Preserve removed registration links too; never overwrite a newer user path."""
    for index, item in reversed(list(enumerate(items))):
        if item.get("restored"):
            continue
        target = Path(item["target"])
        if item.get("linked"):
            if not target.is_symlink() or os.readlink(target) != item["source"]:
                raise SetupError(f"Target changed after apply; refusing restore: {target}")
            backup_move(target, folder / "retired-links" / str(index))
            item["linked"] = False
            checkpoint()
        elif exists(target) and item.get("backed_up"):
            raise SetupError(f"Target now occupied; refusing restore: {target}")
        if item.get("backed_up"):
            backup = Path(item["backup"])
            if not exists(backup):
                raise SetupError(f"Missing backup: {backup}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup), str(target))
            item["backed_up"] = False
            checkpoint()
        item["restored"] = True
        checkpoint()


def apply(root, home, machine, engines, selected, replace, retire, native_disabled):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", machine or ""):
        raise SetupError("Supply --machine with a unique host/guest label")
    data = plan(root, home, engines, selected, machine)
    preflight(data, replace, retire, native_disabled)
    changed = [op for op in data["operations"] if op["state"] != "linked" or op["legacy_duplicates"]]
    if not changed:
        return {"receipt": None, "changed": [], "status": "already linked", "runtime_discovery": "untested"}
    with mutation_lock(root, home):
        data = plan(root, home, engines, selected, machine)
        preflight(data, replace, retire, native_disabled)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]
        folder = state_directory(root) / machine / stamp
        folder.mkdir(parents=True, exist_ok=False)
        receipt_path = folder / "receipt.json"
        receipt = {"schema_version": 1, "root": str(root), "home": str(home),
            "machine": machine, "status": "in_progress", "operations": [],
            "native_disabled_attestation": list(native_disabled)}
        save_receipt(receipt_path, receipt)
        retired = set()
        try:
            for operation in data["operations"]:
                prepare_ledger(operation)
                for old in operation["legacy_duplicates"]:
                    if old in retired:
                        continue
                    retired.add(old)
                    item = {"target": old, "source": None, "backed_up": False, "linked": False,
                            "backup": str(folder / "backups" / str(len(receipt["operations"])))}
                    receipt["operations"].append(item)
                    save_receipt(receipt_path, receipt)
                    backup_move(Path(old), Path(item["backup"]))
                    item["backed_up"] = True
                    save_receipt(receipt_path, receipt)
                if operation["state"] == "linked":
                    continue
                target = Path(operation["target"])
                item = {"target": str(target), "source": operation["source"],
                    "backup": str(folder / "backups" / str(len(receipt["operations"]))),
                    "backed_up": False, "linked": False}
                receipt["operations"].append(item)
                save_receipt(receipt_path, receipt)
                check_parents(target, home)
                if exists(target):
                    if not replace:
                        raise SetupError(f"Target appeared during apply: {target}")
                    backup_move(target, Path(item["backup"]))
                    item["backed_up"] = True
                    save_receipt(receipt_path, receipt)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(operation["source"])
                item["linked"] = True
                save_receipt(receipt_path, receipt)
                if not target.exists() or target.resolve() != Path(item["source"]).resolve():
                    raise SetupError(f"New link does not resolve: {target}")
            receipt["status"] = "applied"
            save_receipt(receipt_path, receipt)
        except BaseException as exc:
            try:
                undo_items(receipt["operations"], folder, lambda: save_receipt(receipt_path, receipt))
                receipt["status"] = "rolled_back"
            except BaseException as restore_error:
                receipt["status"] = "recovery_required"
                receipt["recovery_error"] = str(restore_error)
            receipt["error"] = str(exc)
            save_receipt(receipt_path, receipt)
            raise SetupError(f"Apply failed ({receipt['status']}); receipt: {receipt_path}; {exc}") from exc
    return {"receipt": str(receipt_path), "changed": receipt["operations"],
            "status": "linked", "runtime_discovery": "untested; inspect a fresh agent session"}


def restore(root, home, receipt_value):
    path = Path(receipt_value).expanduser().resolve()
    base = state_directory(root).resolve()
    if not path.is_relative_to(base) or path.name != "receipt.json":
        raise SetupError("Receipt must be inside this checkout's global/registrations")
    with mutation_lock(root, home):
        receipt = read_json(path)
        if receipt.get("root") != str(root) or receipt.get("home") != str(home):
            raise SetupError("Receipt belongs to a different checkout or home")
        if receipt.get("status") == "restored":
            return {"status": "already restored", "receipt": str(path)}
        if receipt.get("status") not in ("applied", "recovery_required"):
            raise SetupError("Receipt was not fully applied; inspect its recovery journal")
        for item in receipt["operations"]:
            target = target_path(home, str(Path(item["target"]).relative_to(home)))
            backup = Path(item["backup"])
            if not backup.parent.resolve().is_relative_to(path.parent):
                raise SetupError("Backup escapes its receipt directory")
            if item.get("restored"):
                continue
            if item["linked"]:
                if not target.is_symlink() or os.readlink(target) != item["source"]:
                    raise SetupError(f"Target changed after apply; refusing restore: {target}")
            elif exists(target):
                raise SetupError(f"Retired target is now occupied: {target}")
            if item["backed_up"] and not exists(backup):
                raise SetupError(f"Missing backup: {backup}")
        try:
            undo_items(receipt["operations"], path.parent, lambda: save_receipt(path, receipt))
        except BaseException as exc:
            receipt["status"] = "recovery_required"
            receipt["recovery_error"] = str(exc)
            save_receipt(path, receipt)
            raise SetupError(f"Restore failed (recovery_required); retry after resolving the error; receipt: {path}; {exc}") from exc
        receipt["status"] = "restored"
        save_receipt(path, receipt)
    return {"status": "restored", "receipt": str(path)}


def inventory(root, home):
    directories = (".agents/skills", ".codex/skills", ".claude/skills", ".claude/commands")
    result = {}
    for relative in directories:
        directory = home / relative
        result[relative] = [] if not directory.is_dir() else [
            {"name": p.name, "symlink": p.is_symlink(),
             "link_target": os.readlink(p) if p.is_symlink() else None}
            for p in sorted(directory.iterdir())]
    return {"root": str(root), "home": str(home), "discovery_directories": result,
            "registered_skills": list(definitions(root)),
            "note": "Filesystem inventory; active plugin/session inventory must be checked in the target tool"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--machine")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory")
    for name in ("plan", "status", "apply"):
        command = sub.add_parser(name)
        command.add_argument("--engine", choices=("codex", "claude", "both"), required=True)
        command.add_argument("--skill", action="append", default=[])
        if name == "apply":
            command.add_argument("--confirm", action="store_true")
            command.add_argument("--replace", action="store_true")
            command.add_argument("--retire-legacy", action="store_true")
            command.add_argument("--native-disabled", action="append", default=[])
    command = sub.add_parser("restore")
    command.add_argument("--receipt", required=True)
    command.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    root, home = Path(args.root).expanduser().resolve(), Path(args.home).expanduser().resolve()
    try:
        if args.command in ("apply", "restore") and not args.confirm:
            raise SetupError("Mutation requires explicit --confirm after review and selection")
        if args.command == "inventory":
            result = inventory(root, home)
        elif args.command == "restore":
            result = restore(root, home, args.receipt)
        else:
            engines = ("codex", "claude") if args.engine == "both" else (args.engine,)
            if args.command == "apply":
                result = apply(root, home, args.machine, engines, args.skill, args.replace,
                               args.retire_legacy, args.native_disabled)
            else:
                result = plan(root, home, engines, args.skill, args.machine)
        print(json.dumps(result, indent=2))
        if args.command == "status":
            return 0 if all(op["state"] == "linked" and op["source_available"] and not op["legacy_duplicates"]
                            and op["dependency_selected"]
                            and (not op["source_integrity"] or op["source_integrity"]["status"] == "verified")
                            and not op["potential_plugin_caches"]
                            for op in result["operations"]) else 1
        return 0
    except (SetupError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
