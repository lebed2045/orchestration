#!/usr/bin/env python3
"""Deterministic scenario coverage and web-app verification gate."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


CONFIG_REL = Path(".agent-verification/config.json")
RUNS_REL = Path(".agent-verification/runs")
SCENARIO_RE = re.compile(r"^##\s+([A-Z][A-Z0-9_-]*-\d+):\s+\S", re.MULTILINE)
MARKER_RE = re.compile(r"SCENARIO:\s*([A-Z][A-Z0-9_-]*-\d+)\b")
TEST_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".feature"}


class VerificationError(RuntimeError):
    pass


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _write_new(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _asset(name: str) -> str:
    return (Path(__file__).resolve().parent.parent / "assets" / name).read_text(encoding="utf-8")


def _install_project_hooks(root: Path) -> bool:
    path = root / ".codex/hooks.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise VerificationError(f"cannot merge invalid {path.relative_to(root)}: {exc}") from exc
    else:
        data = {"hooks": {}}
    hooks = data.setdefault("hooks", {})
    command = 'python3 "$HOME/.codex/skills/in-browser-verify/scripts/codex_in_browser_gate.py"'
    command_windows = 'py -3 "%USERPROFILE%\\.codex\\skills\\in-browser-verify\\scripts\\codex_in_browser_gate.py"'
    desired = {
        "SessionStart": ("Loading in-browser verification contract",),
        "Stop": ("Checking in-browser verification evidence",),
    }
    changed = False
    for event, (status,) in desired.items():
        groups = hooks.setdefault(event, [])
        exists = any(
            item.get("command") == command
            for group in groups if isinstance(group, dict)
            for item in group.get("hooks", []) if isinstance(item, dict)
        )
        if not exists:
            groups.append({"hooks": [{
                "type": "command",
                "command": command,
                "commandWindows": command_windows,
                "timeout": 30,
                "statusMessage": status,
            }]})
            changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def init_repo(root: Path) -> int:
    created = []
    if _write_new(root / CONFIG_REL, _asset("config.example.json")):
        created.append(str(CONFIG_REL))
    scenario_path = root / "verification/scenarios.md"
    if _write_new(scenario_path, _asset("scenarios.example.md")):
        created.append("verification/scenarios.md")
    if _install_project_hooks(root):
        created.append(".codex/hooks.json")
    if created:
        print("Created: " + ", ".join(created))
        print("Customize commands, scenarios, Playwright trace policy, and deterministic test state before running the gate.")
        print("Project-local hooks activate only for this onboarded repository; review them with /hooks in a new session.")
    else:
        print("No files changed; verification config and scenario ledger already exist.")
    return 0


def _load_config(root: Path) -> tuple[dict, Path]:
    path = root / CONFIG_REL
    if not path.is_file():
        raise VerificationError(f"missing {CONFIG_REL}; run init first")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid {CONFIG_REL}: {exc}") from exc
    if config.get("version") != 1:
        raise VerificationError("config version must be 1")
    return config, path


def _validate_config(root: Path, config: dict) -> None:
    scenario_file = config.get("scenario_file")
    test_roots = config.get("test_roots")
    commands = config.get("commands")
    evidence = config.get("evidence")
    if not isinstance(scenario_file, str) or not scenario_file:
        raise VerificationError("scenario_file must be a non-empty string")
    if not (root / scenario_file).is_file():
        raise VerificationError(f"scenario file not found: {scenario_file}")
    if not isinstance(test_roots, list) or not test_roots or not all(isinstance(x, str) and x for x in test_roots):
        raise VerificationError("test_roots must be a non-empty string array")
    if not isinstance(commands, list) or not commands:
        raise VerificationError("commands must be a non-empty array")
    seen_names = set()
    for item in commands:
        if not isinstance(item, dict):
            raise VerificationError("every command must be an object")
        name, argv = item.get("name"), item.get("argv")
        if not isinstance(name, str) or not name or name in seen_names:
            raise VerificationError("command names must be unique non-empty strings")
        seen_names.add(name)
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise VerificationError(f"command {name!r} argv must be a non-empty string array")
        timeout = item.get("timeout_seconds", 600)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise VerificationError(f"command {name!r} timeout_seconds must be positive")
    if not isinstance(evidence, dict):
        raise VerificationError("evidence must be an object")
    patterns = evidence.get("required_globs")
    if not isinstance(patterns, list) or not patterns or not all(isinstance(x, str) and x for x in patterns):
        raise VerificationError("evidence.required_globs must be a non-empty string array")
    minimum = evidence.get("minimum_files", 1)
    if not isinstance(minimum, int) or minimum < 1:
        raise VerificationError("evidence.minimum_files must be a positive integer")


def _scenario_coverage(root: Path, config: dict) -> dict:
    scenario_path = root / config["scenario_file"]
    scenario_text = scenario_path.read_text(encoding="utf-8")
    required = SCENARIO_RE.findall(scenario_text)
    if not required:
        raise VerificationError(f"no scenario headings found in {config['scenario_file']}")
    if len(required) != len(set(required)):
        duplicates = sorted({x for x in required if required.count(x) > 1})
        raise VerificationError("duplicate scenario IDs: " + ", ".join(duplicates))

    mapped: dict[str, list[str]] = {}
    scanned_files = 0
    for rel_root in config["test_roots"]:
        test_root = root / rel_root
        if not test_root.is_dir():
            continue
        for path in test_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEST_SUFFIXES:
                continue
            scanned_files += 1
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for scenario_id in MARKER_RE.findall(text):
                mapped.setdefault(scenario_id, []).append(str(path.relative_to(root)))

    missing = sorted(set(required) - set(mapped))
    unknown = sorted(set(mapped) - set(required))
    if missing:
        raise VerificationError("scenarios without executable test markers: " + ", ".join(missing))
    if unknown:
        raise VerificationError("test markers absent from scenario ledger: " + ", ".join(unknown))
    return {
        "required": required,
        "mapped": mapped,
        "required_count": len(required),
        "covered_count": len(required),
        "scanned_test_files": scanned_files,
    }


def check_repo(root: Path) -> tuple[dict, dict, Path]:
    config, config_path = _load_config(root)
    _validate_config(root, config)
    coverage = _scenario_coverage(root, config)
    return config, coverage, config_path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_sha(root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def workspace_fingerprint(root: Path) -> str:
    """Hash HEAD plus tracked/untracked working-tree content, excluding run output."""
    digest = hashlib.sha256()
    digest.update((_git_sha(root) or "no-git-head").encode())
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        digest.update(b"no-git-status")
        return digest.hexdigest()
    paths = []
    for record in proc.stdout.split(b"\0"):
        if not record:
            continue
        text = record.decode("utf-8", errors="surrogateescape")
        path_text = text[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        path = Path(path_text)
        if path.parts[:2] == (".agent-verification", "runs"):
            continue
        paths.append(path)
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path).encode("utf-8", errors="surrogateescape"))
        absolute = root / path
        if absolute.is_file():
            digest.update(absolute.read_bytes())
        else:
            digest.update(b"<deleted-or-non-file>")
    return digest.hexdigest()


def _run_command(root: Path, run_dir: Path, command: dict) -> dict:
    name = command["name"]
    argv = list(command["argv"])
    resolved = shutil.which(argv[0])
    if resolved:
        argv[0] = resolved
    timeout = float(command.get("timeout_seconds", 600))
    log_path = run_dir / f"{name}.log"
    started = _utc_now()
    start_clock = time.monotonic()
    env = os.environ.copy()
    extra_env = command.get("env", {})
    if not isinstance(extra_env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in extra_env.items()):
        raise VerificationError(f"command {name!r} env must be a string map")
    env.update(extra_env)
    try:
        proc = subprocess.run(
            argv,
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = proc.stdout
        exit_code = proc.returncode
        timed_out = False
    except FileNotFoundError as exc:
        output = str(exc)
        exit_code = 127
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + f"\nTIMEOUT after {timeout:g}s\n"
        exit_code = 124
        timed_out = True
    log_path.write_text(output, encoding="utf-8")
    return {
        "name": name,
        "argv": argv,
        "started_at": started.isoformat(),
        "duration_seconds": round(time.monotonic() - start_clock, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "log": str(log_path.relative_to(root)),
    }


def _evidence_snapshot(root: Path, config: dict) -> dict[str, str]:
    evidence = config["evidence"]
    found: dict[str, str] = {}
    for pattern in evidence["required_globs"]:
        for raw in glob.glob(str(root / pattern), recursive=True):
            path = Path(raw)
            if path.is_file():
                resolved = path.resolve()
                found[str(resolved)] = _sha256(resolved)
    return found


def _fresh_evidence(root: Path, config: dict, before: dict[str, str]) -> list[str]:
    evidence = config["evidence"]
    after = _evidence_snapshot(root, config)
    found = {
        Path(path) for path, digest in after.items()
        if path not in before or before[path] != digest
    }
    minimum = evidence.get("minimum_files", 1)
    if len(found) < minimum:
        raise VerificationError(
            f"fresh browser evidence missing: found {len(found)}, require {minimum}; "
            f"patterns={evidence['required_globs']}"
        )
    return sorted(str(path.relative_to(root.resolve())) for path in found)


def run_repo(root: Path) -> int:
    config, coverage, config_path = check_repo(root)
    started = _utc_now()
    evidence_before = _evidence_snapshot(root, config)
    run_id = started.strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = root / RUNS_REL / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "running",
        "started_at": started.isoformat(),
        "git_sha": _git_sha(root),
        "config": str(config_path.relative_to(root)),
        "config_sha256": _sha256(config_path),
        "scenario_file": config["scenario_file"],
        "scenario_file_sha256": _sha256(root / config["scenario_file"]),
        "coverage": coverage,
        "commands": [],
        "evidence": [],
    }
    manifest_path = run_dir / "manifest.json"

    try:
        for command in config["commands"]:
            result = _run_command(root, run_dir, command)
            manifest["commands"].append(result)
            if result["exit_code"] != 0:
                raise VerificationError(f"command {result['name']!r} failed with exit {result['exit_code']}")
        manifest["evidence"] = _fresh_evidence(root, config, evidence_before)
        manifest["workspace_fingerprint"] = workspace_fingerprint(root)
        manifest["status"] = "passed"
        exit_code = 0
    except VerificationError as exc:
        manifest["status"] = "failed"
        manifest["failure"] = str(exc)
        exit_code = 1
    finally:
        manifest["finished_at"] = _utc_now().isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"WEB_VERIFICATION: {'VERIFIED' if exit_code == 0 else 'UNVERIFIED'}")
    print(f"Scenarios: {coverage['covered_count']}/{coverage['required_count']}")
    print(f"Manifest: {manifest_path.relative_to(root)}")
    if exit_code:
        print(f"Failure: {manifest.get('failure')}", file=sys.stderr)
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "check", "run"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "init":
            return init_repo(root)
        if args.command == "check":
            _, coverage, _ = check_repo(root)
            print(f"WEB_VERIFY_CHECK: PASS ({coverage['covered_count']}/{coverage['required_count']} scenarios mapped)")
            return 0
        return run_repo(root)
    except VerificationError as exc:
        print(f"WEB_VERIFY_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
