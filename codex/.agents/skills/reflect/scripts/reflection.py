#!/usr/bin/env python3
"""Record Codex reflection incidents and maintain live AGENTS.md rules."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SYSTEM_START = "<!-- CODEX-REFLECT-SYSTEM:START -->"
SYSTEM_END = "<!-- CODEX-REFLECT-SYSTEM:END -->"
RULES_START = "<!-- CODEX-REFLECT-RULES:START -->"
RULES_END = "<!-- CODEX-REFLECT-RULES:END -->"
PATTERN_PREFIX = "<!-- reflect-pattern: "

SYSTEM_TEXT = f"""{SYSTEM_START}
Whenever Codex makes a confirmed mistake, the user corrects it, or verification disproves its claim, stop before continuing the task and use `$reflect`: write a short postmortem, check recurrence, create or strengthen a WHEN/DO/PROVE rule, update the appropriate `AGENTS.md`, and record the incident. Repeated `pattern_key` values escalate mechanically from L1 reminder to L2 mandatory proof to L3 hard gate to L4 halt.
{SYSTEM_END}"""

RULES_TEXT = f"""{RULES_START}
<!-- Managed by $reflect. Do not edit levels or strike chains by hand. -->
{RULES_END}"""

REQUIRED_FIELDS = (
    "trigger",
    "what",
    "root_cause",
    "impact",
    "correction",
    "pattern_key",
    "rule_title",
    "when",
    "do",
    "prove",
    "pillar",
    "reviewer",
)

LEVEL_LABELS = {
    1: "L1 REMINDER",
    2: "L2 MANDATORY PROOF",
    3: "L3 HARD GATE",
    4: "L4 HALT",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()


def project_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise SystemExit("project scope requires --project-root or a git worktree")
    return Path(result.stdout.strip()).resolve()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def commit_updates(updates: dict[Path, str]) -> None:
    originals = {path: read_text(path) if path.exists() else None for path in updates}
    written: list[Path] = []
    try:
        for path, content in updates.items():
            atomic_write(path, content)
            written.append(path)
    except BaseException:
        rollback_errors: list[str] = []
        for path in reversed(written):
            try:
                original = originals[path]
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, original)
            except BaseException as rollback_error:
                rollback_errors.append(f"{path}: {rollback_error}")
        if rollback_errors:
            print("ROLLBACK_FAILED: " + " | ".join(rollback_errors), file=sys.stderr)
        raise


def append_content(existing: str, addition: str) -> str:
    if not existing:
        return addition.rstrip() + "\n"
    return existing.rstrip() + "\n\n" + addition.rstrip() + "\n"


def append_json_line(existing: str, line: str) -> str:
    if not existing:
        return line.rstrip() + "\n"
    return existing.rstrip() + "\n" + line.rstrip() + "\n"


def ensure_contract(content: str) -> str:
    additions: list[str] = []
    if SYSTEM_START in content and SYSTEM_END in content:
        start = content.index(SYSTEM_START)
        end = content.index(SYSTEM_END, start) + len(SYSTEM_END)
        content = content[:start] + SYSTEM_TEXT + content[end:]
    else:
        additions.append("# Reflection after confirmed mistakes\n\n" + SYSTEM_TEXT)
    if RULES_START not in content:
        additions.append(RULES_TEXT)
    if additions:
        return append_content(content, "\n\n".join(additions))
    return content


def validate_input(data: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not str(data.get(field, "")).strip()]
    if missing:
        raise SystemExit(f"missing required fields: {', '.join(missing)}")
    key = str(data["pattern_key"])
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key):
        raise SystemExit("pattern_key must be stable kebab-case")
    for field in ("what", "root_cause", "impact", "correction"):
        if "\n" in str(data[field]).strip():
            raise SystemExit(f"{field} must be one line")


def read_incidents(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    incidents: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            incidents.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSON in {path}:{line_number}: {exc}") from exc
    return incidents


def git_value(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def project_prefix(root: Path) -> str:
    code = re.sub(r"[^A-Za-z0-9]", "", root.name).upper()[:4] or "PROJ"
    branch = git_value(root, "branch", "--show-current")
    commit = git_value(root, "rev-parse", "--short=6", "HEAD")
    parts = [code]
    if branch:
        parts.append(re.sub(r"[^A-Za-z0-9._/-]+", "-", branch))
    if commit:
        parts.append(commit)
    return "-".join(parts)


def next_id(scope: str, incidents: list[dict[str, Any]], root: Path | None) -> str:
    prefix = "GLO" if scope == "global" else project_prefix(root or Path.cwd())
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    numbers = [int(match.group(1)) for item in incidents if (match := pattern.match(str(item.get("id", ""))))]
    return f"{prefix}-{max(numbers, default=0) + 1}"


def escalation(incidents: list[dict[str, Any]], pattern_key: str) -> tuple[int, str | None, list[str]]:
    matches = [item for item in incidents if item.get("pattern_key") == pattern_key]
    if not matches:
        return 1, None, []
    previous = matches[-1]
    previous_level = int(str(previous.get("level", "L1")).removeprefix("L"))
    return min(previous_level + 1, 4), str(previous["id"]), [str(item["id"]) for item in matches]


def rule_block(data: dict[str, Any], incident_id: str, level: int, strikes: list[str]) -> str:
    key = data["pattern_key"]
    lines = [
        f"{PATTERN_PREFIX}{key} -->",
        f"### {data['rule_title']} (ref: {incident_id})",
        f"**[{LEVEL_LABELS[level]}]**" + (f" Strikes: {' -> '.join(strikes + [incident_id])}." if level > 1 else ""),
        f"WHEN {str(data['when']).rstrip('.')}:" ,
        f"DO {str(data['do']).rstrip('.')}.",
        f"PROVE {str(data['prove']).rstrip('.')}.",
    ]
    if level == 3:
        lines.append("GATE Do not continue the triggering task until that proof is visible in the current turn.")
    elif level >= 4:
        lines.append("HALT Do not continue the triggering task; report the strike chain and request manual intervention.")
    return "\n".join(lines)


def upsert_rule(content: str, pattern_key: str, block: str) -> str:
    content = ensure_contract(content)
    start = content.index(RULES_START) + len(RULES_START)
    end = content.index(RULES_END, start)
    body = content[start:end].strip("\n")
    marker = f"{PATTERN_PREFIX}{pattern_key} -->"
    marker_at = body.find(marker)
    if marker_at >= 0:
        next_marker = body.find(PATTERN_PREFIX, marker_at + len(marker))
        replacement_end = next_marker if next_marker >= 0 else len(body)
        body = body[:marker_at].rstrip() + "\n\n" + block + "\n\n" + body[replacement_end:].lstrip()
    else:
        body = body.rstrip() + "\n\n" + block
    updated = content[:start] + "\n" + body.strip() + "\n" + content[end:]
    return updated.rstrip() + "\n"


def targets(scope: str, home: Path, root: Path | None) -> tuple[Path, Path]:
    if scope == "global":
        return home / "AGENTS.md", home / "reflections"
    assert root is not None
    return root / "AGENTS.md", root / ".codex" / "reflections"


def incident_record(
    data: dict[str, Any],
    incident_id: str,
    timestamp: str,
    scope: str,
    level: int,
    recurrence_of: str | None,
) -> dict[str, Any]:
    return {
        "id": incident_id,
        "ts": timestamp,
        "agent": "codex",
        "trigger": data["trigger"],
        "what": data["what"],
        "root_cause": data["root_cause"],
        "impact": data["impact"],
        "correction": data["correction"],
        "pattern_key": data["pattern_key"],
        "rule_id": data["rule_title"],
        "level": f"L{level}",
        "recurrence_of": recurrence_of,
        "pillar": data["pillar"],
        "scope": scope,
        "reviewer": data["reviewer"],
    }


def ledger_updates(
    ledger: Path,
    data: dict[str, Any],
    incident: dict[str, Any],
    block: str,
    agents_path: Path,
) -> dict[Path, str]:
    incident_id = incident["id"]
    date = str(incident["ts"])[:10]
    recurrence = incident["recurrence_of"] or "none"
    context = data.get("context") or "Confirmed Codex failure during the active user task."
    json_line = json.dumps(incident, ensure_ascii=False, separators=(",", ":"))

    failures = f"""## {incident_id} | {date} | {incident['scope']}

**Context:** {context}
**Failure:** {incident['what']}
**Root cause:** {incident['root_cause']}
**Impact:** {incident['impact']}
**Immediate correction:** {incident['correction']}
**Rule:** WHEN {data['when']} DO {data['do']} PROVE {data['prove']}
"""
    addressed = f"""## {incident_id} | ADDRESSED | {date}

**What happened:** {incident['what']}
**Root cause:** {incident['root_cause']}
**Rule added:** {agents_path} -> \"{data['rule_title']}\"
**Pattern:** {incident['pattern_key']}
**Escalation:** {incident['level']}
**Recurrence of:** {recurrence}
**Reviewed by:** {incident['reviewer']}
**Status:** MONITORING
"""
    permanent = f"""## {incident_id} | {incident['ts']} | {incident['level']} | scope={incident['scope']} | reviewed={incident['reviewer']}

**What:** {incident['what']}
**Root cause:** {incident['root_cause']}
**Impact:** {incident['impact']}
**Correction:** {incident['correction']}
**Pattern:** {incident['pattern_key']}
**Recurrence of:** {recurrence}
**Rule (verbatim as added to AGENTS.md):**
{block}

---
"""
    return {
        ledger / "incidents.jsonl": append_json_line(read_text(ledger / "incidents.jsonl"), json_line),
        ledger / "failures.md": append_content(read_text(ledger / "failures.md"), failures),
        ledger / "failures-addressed.md": append_content(read_text(ledger / "failures-addressed.md"), addressed),
        ledger / "reflection-log.md": append_content(read_text(ledger / "reflection-log.md"), permanent),
    }


def command_install(args: argparse.Namespace) -> int:
    home = codex_home(args.codex_home)
    skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else Path.home() / ".agents" / "skills"
    skill = Path(__file__).resolve().parent.parent
    link = skills_root / "reflect"
    skills_root.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() and link.resolve() != skill:
        raise SystemExit(f"refusing to replace unrelated symlink: {link}")
    if link.exists() and not link.is_symlink() and link.resolve() != skill:
        raise SystemExit(f"refusing to replace existing path: {link}")
    if not link.exists():
        link.symlink_to(skill, target_is_directory=True)
        print(f"Installed global skill link: {link} -> {skill}")
    else:
        print(f"Global skill link already installed: {link}")
    agents = home / "AGENTS.md"
    updated = ensure_contract(read_text(agents))
    if updated != read_text(agents):
        atomic_write(agents, updated)
        print(f"Installed reflection contract: {agents}")
    else:
        print(f"Reflection contract already installed: {agents}")
    return 0


def command_record(args: argparse.Namespace) -> int:
    home = codex_home(args.codex_home)
    root = project_root(args.project_root) if args.scope == "project" else None
    agents_path, ledger = targets(args.scope, home, root)
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_input(data)
    incidents = read_incidents(ledger / "incidents.jsonl")
    incident_id = next_id(args.scope, incidents, root)
    level, recurrence_of, prior_strikes = escalation(incidents, data["pattern_key"])
    timestamp = utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")
    block = rule_block(data, incident_id, level, prior_strikes)
    incident = incident_record(data, incident_id, timestamp, args.scope, level, recurrence_of)
    agents_updated = upsert_rule(read_text(agents_path), data["pattern_key"], block)
    updates = {agents_path: agents_updated, **ledger_updates(ledger, data, incident, block, agents_path)}

    if args.dry_run:
        print(f"DRY RUN: {incident_id} {incident['level']} recurrence_of={recurrence_of or 'none'}")
        print(f"Target: {agents_path}")
        print(block)
        return 0

    commit_updates(updates)
    print(f"RECORDED: {incident_id}")
    print(f"LEVEL: {incident['level']}")
    print(f"RECURRENCE_OF: {recurrence_of or 'none'}")
    print(f"RULE: {agents_path}")
    print(f"LEDGER: {ledger}")
    size = len(agents_updated.encode("utf-8"))
    print(f"AGENTS_SIZE: {size}")
    if size > 30000:
        print("SIZE_GATE: COMPRESSION_REQUIRED")
    return 0


def command_list(args: argparse.Namespace) -> int:
    home = codex_home(args.codex_home)
    root = project_root(args.project_root) if args.scope == "project" else None
    _, ledger = targets(args.scope, home, root)
    incidents = read_incidents(ledger / "incidents.jsonl")
    if not incidents:
        print(f"No {args.scope} Codex reflection incidents.")
        return 0
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for incident in incidents:
        groups[str(incident.get("pattern_key", "legacy-unclassified"))].append(incident)
    print("PATTERN\tLEVEL\tSTRIKES\tNEXT")
    for key, items in sorted(groups.items()):
        last = items[-1]
        level = int(str(last.get("level", "L1")).removeprefix("L"))
        next_label = LEVEL_LABELS[min(level + 1, 4)]
        chain = " -> ".join(str(item["id"]) for item in items)
        print(f"{key}\tL{level}\t{chain}\t{next_label}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser("install", help="install global skill discovery and reflection contract")
    install.add_argument("--codex-home")
    install.add_argument("--skills-root")
    install.set_defaults(func=command_install)

    record = subparsers.add_parser("record", help="record an incident and update the live rule")
    record.add_argument("--scope", choices=("global", "project"), required=True)
    record.add_argument("--input", required=True)
    record.add_argument("--codex-home")
    record.add_argument("--project-root")
    record.add_argument("--dry-run", action="store_true")
    record.set_defaults(func=command_record)

    listing = subparsers.add_parser("list", help="show patterns and escalation state without writing")
    listing.add_argument("--scope", choices=("global", "project"), required=True)
    listing.add_argument("--codex-home")
    listing.add_argument("--project-root")
    listing.set_defaults(func=command_list)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
