# global/ — rules and reflections shared by every agent

Updated: 05-nov-2026. Claude Code and Codex, on the host and in the VM.

```
global/
├── AGENTS.md          the only global rules file (public)
├── README.md          this file (public)
├── inbox/             NOT reviewed yet — one folder per agent
│   └── {host,vm}-{claude,codex}/reflections/
├── archive/           reviewed history (private)
│   ├── <YYYY-MM-DD>/  one per finished review: AGENTS.md after it + the inbox files it consumed + review.md
│   ├── applied/       before-copies + receipts written by `reflection.py apply`
│   └── 2026-11-05-pre-cleanup/   everything from before this layout (old log/, _incoming/, rules snapshots)
└── registrations/     link receipts from scripts/skills.py (machine state, private; needed for restore)
```

## How an agent finds it

Run `bash scripts/link-globals.sh link` once per machine (status: `… status`). It links:

- `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md` → `AGENTS.md`
- `~/.claude/reflections`, `~/.codex/reflections` → `inbox/<host|vm>-<agent>/reflections`

Old link targets are moved to `~/.agent-link-backups/<time>/`, never deleted. If the share isn't mounted, links show `DANGLING` and agents start without global rules.

## Cycle

record → review → apply → renew. Full guide: `../docs/reflection.md`.

## Keeping AGENTS.md lean

- Budget: the number in its second line. One line per rule, no incident stories, no IDs.
- At the budget, a new line replaces or merges an existing one.
- Edit `AGENTS.md` itself, never the links to it.
