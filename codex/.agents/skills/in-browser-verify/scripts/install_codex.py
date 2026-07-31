#!/usr/bin/env python3
"""Install global skill discovery and Codex lifecycle hooks idempotently."""

from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> int:
    skill = Path(__file__).resolve().parent.parent
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    skills_dir = codex_home / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    old_link = skills_dir / "web-verify"
    if old_link.is_symlink():
        old_link.unlink()
        print(f"Removed renamed skill link: {old_link}")
    link = skills_dir / "in-browser-verify"
    if link.is_symlink() and link.resolve() != skill:
        raise SystemExit(f"refusing to replace unrelated symlink: {link}")
    if link.exists() and not link.is_symlink() and link.resolve() != skill:
        raise SystemExit(f"refusing to replace existing path: {link}")
    if not link.exists():
        link.symlink_to(skill, target_is_directory=True)
        print(f"Installed global skill link: {link} -> {skill}")
    else:
        print(f"Global skill link already installed: {link}")

    # Older versions installed lifecycle hooks globally. Remove those entries:
    # hooks now belong only in web repositories created by `init`.
    hooks_path = codex_home / "hooks.json"
    if hooks_path.exists():
        data = json.loads(hooks_path.read_text(encoding="utf-8"))
        hooks = data.get("hooks", {})
        changed = False
        for event in list(hooks):
            groups = hooks[event]
            if not isinstance(groups, list):
                continue
            kept_groups = []
            for group in groups:
                if not isinstance(group, dict):
                    kept_groups.append(group)
                    continue
                handlers = group.get("hooks", [])
                kept = [
                    item for item in handlers
                    if not any(marker in str(item.get("command", "")) for marker in (
                        "web-verify/scripts/codex_web_gate.py",
                        "in-browser-verify/scripts/codex_in_browser_gate.py",
                    ))
                ]
                changed = changed or len(kept) != len(handlers)
                if kept:
                    updated = dict(group)
                    updated["hooks"] = kept
                    kept_groups.append(updated)
            if kept_groups:
                hooks[event] = kept_groups
            else:
                hooks.pop(event, None)
        if changed:
            if data == {"hooks": {}}:
                hooks_path.unlink()
                print(f"Removed obsolete global hooks file: {hooks_path}")
            else:
                hooks_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                print(f"Removed obsolete in-browser-verify hooks from: {hooks_path}")
    print("Global discovery installed. Project-local hooks are added only by `init` inside a web repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
