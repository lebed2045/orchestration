# Orchestration

Orchestration workflows for coding agents that force TDD, independent review where available, and verifiable completion.

## Install

Open Claude Code in any project and paste this (edit the bracketed parts):

```
Check the orchestration repo at https://github.com/lebed2045/orchestration. Read its
README, CLAUDE.md, and the files in .claude/commands and .claude/agents, then install
the workflow skills for me — into ~/.claude/ so they work in every project [or into
this project's .claude/ if I say so]. Adapt paths and conventions to my setup, and
interview me about my stack first. The Codex and Antigravity reviewers are optional and
need local MCP servers — set those up only if I confirm, and securely: local stdio
servers only, no API keys in MCP config, no committed credentials. Show me a diff before
changing any of my existing files.
```

Restart Claude Code and the commands appear (`/workflow`, `/sweep`, `/research`, …).

### What gets installed

| Goes to | Files | Purpose |
|---|---|---|
| `~/.claude/commands/` | `workflow.md`, `wf.md`, `sweep.md`, `gardener.md`, `research.md`, `r.md`, `think.md`, `reflect.md`, `tl.md` | the slash commands |
| `~/.claude/agents/` | `simplicity-cop.md`, `coherence-cop.md`, `coverage-cop.md`, `metrics-cop.md`, … | reviewer sub-agents `/wf` spawns |
| `~/.claude/reference/` | `code-quality-metrics.md` | metrics-cop threshold source-of-truth |
| `~/.claude/skills/tldr/` | `SKILL.md` | the `/tl` summarizer |

`~/.claude/` = available in every project. A project's `.claude/` = that repo only, and it wins when both define the same name. `/wf` and `/gardener` write per-project longitudinal ledgers (`ratchet.tsv`, `debt.tsv`) into the project's `.claude/metrics/` — those stay in the project, not global.

Settings (`MCP_TIMEOUT`/`MCP_TOOL_TIMEOUT`, the allowed MCP tools, etc.) are not shipped — `settings.local.json` is gitignored. Tell the installer to add only what you want into your own `~/.claude/settings.json`.

The base workflows run with **no MCP at all** — the optional reviewers just downgrade and say so. The MCP setup below is opt-in.

## MCP setup (optional, secure)

Two reviewers use **local stdio** MCP servers — they run a command on your machine, not a remote URL. That's the safer shape: nothing is hosted off-box and you can read the code before you trust it.

**Codex reviewer (`-c`, default-on in `/wf`)** — the official Codex CLI's built-in MCP server:

```
claude mcp add --transport stdio --scope user codex-cli -- codex mcp-server
```

Needs the `codex` CLI installed and logged in. It authenticates with its own session — **no API key goes into MCP config**.

**Antigravity reviewer (`-g`, opt-in)** — a small local Python bridge to Gemini. Read the bridge source before adding it, then register your local script as a stdio server.

Security checklist for any MCP server:

- **Local stdio over remote.** Prefer a command you can audit; be wary of remote MCP URLs.
- **No secrets in config.** Don't paste API keys/tokens into the MCP entry — use the tool's own login (Codex) or environment variables.
- **Credentials stay out of the repo.** Any service-account key lives outside the working tree, `chmod 600`, never committed (this repo keeps key paths out of the tree and scrubs them from docs for that reason).
- **Least privilege.** Scope a cloud service account to exactly the API it needs — never Owner/Editor.
- **Read before you add, scope per user.** Review a server's source and deps first. Use `--scope user` for personal servers so a project-level `.mcp.json` never ships your machine paths.

Missing MCP is fine — `/wf` continues with the reviewer downgraded (pass `--abort-on-missing-mcp` if you'd rather it hard-fail).

## Commands

| Command | What it does |
|---|---|
| `/workflow` (`/wf`) | The workflow. Tier-auto TDD on modern primitives. Codex reviewer on by default (`--no-codex` to skip). Prints `workflow v0.27 (19-jun-2026)` as its first line. |
| `/gardener` | Periodic entropy removal. Reads the longitudinal ledgers (`.claude/metrics/ratchet.tsv`, `debt.tsv`), sweeps for duplication / dead code, and executes the top-K cleanups as small `/wf`-style tasks (`--top=K`, `--dry-run`). |
| `/sweep` | End-of-session working-tree sweep. Classifies each uncommitted path (discard/ignore/commit-main/commit-sidecar/stash/hold) and executes so `git status` ends clean. Codex on by default (`--fast` / `--no-codex` to skip); secrets hard-fenced from auto-commit; never pushes. Prints `sweep v1 (13-jun-2026)` as its first line. |
| `/research` (`/r`) | Codebase + agy bridge MCP + Codex MCP research. |
| `/think` | Council-style deliberation for judgment calls, framing critique, and pushback. |
| `/reflect` | Turn recurring failures into rules. |
| `/tl` | Tweet-size summary of the last output + clickable next-action buttons (`tldr` skill). |

Claude research goes in `.claude/research/`. Codex research goes in `codex/research/`.

```text
codex/research/
├── codex-claude-agentic-coding-workflows.md
└── claude-from-codex-c-flag-tos.md
```

## Codex

Codex does not load repo-local `/wf`, `/research`, or `/think` slash commands out of the box. Its repo-shared mechanism is skills, so the Codex equivalents live in:

```text
codex/
├── .agents/
│   └── skills/
│       ├── wf/
│       ├── research/
│       └── think/
├── bin/
├── postmortems/
├── research/
└── temp/        # gitignored scratch
```

Invoke them in Codex as `$wf <task>`, `$research <topic>`, and `$think <topic>`, or choose them from `/skills`. Start a new Codex session if the skills do not appear immediately. Codex custom prompt slash commands exist as `/prompts:<name>`, but they are user-local under `~/.codex/prompts` and deprecated, so this repo uses skills instead.

Older generations are archived in [legacy/](legacy/) (outside `.claude/` so Claude Code doesn't auto-register them as commands). They're kept in the repo as evolutionary context for AI coders reading the codebase, not for invocation.

## Why bother

Vanilla Claude reviews its own work and the review is biased. `/wf` enforces three things vanilla skips: TDD as a gate (RED then GREEN, both verified), zero-context reviewers (no planning history → can't be optimistic), and `EXECUTION_BLOCK` proof (command + output + exit code) before any completion claim. Plus `BASELINE_BLOCK`/`REGRESSION_DELTA` anti-regression. Full rules in [CLAUDE.md](CLAUDE.md).

## Optional reviewers

- `-c` means "the other main model": Claude commands call Codex; Codex skills call Claude.
- `-g` means Gemini / Antigravity through the agy bridge MCP (`mcp__agy__agy_ask`).

Codex `-c` uses the official-Claude bridge at `~/.agents/bin/claude-peer` or `codex/bin/claude-peer`, preferring the user-local copy. It requires Claude Code subscription login (`claude.ai`) and refuses API-key auth, so it uses your Claude quota, not API billing. This is for local personal workflow use; workflows must say clearly when an optional reviewer is unavailable.

The agy bridge first tries `agy`. It detects 429 `RESOURCE_EXHAUSTED` from `agy` stdout/stderr and `~/.gemini/antigravity-cli/log/cli-*.log`; if free Gemini quota is exhausted, the bridge automatically routes the same prompt to a Vertex Gemini model (`gemini-3.5-flash`) using a project, location, and service-account key read from the bridge's own environment — never committed — and prefixes the response with the route. Workflows should treat that as the intended Gemini fallback, not substitute Claude/Codex or inline self-review to avoid Vertex credits. After bridge-code updates, restart the MCP host so the new fallback logic is loaded.

## Thanks

A GitHub star on [lebed2045/orchestration](https://github.com/lebed2045/orchestration) tells me what's worth building more of. PRs welcome. "This didn't work for me" reports are most valuable.

## License

MIT
