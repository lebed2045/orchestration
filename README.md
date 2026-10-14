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

Restart Claude Code and the commands appear (`/workflow`, `/manager`, `/research`, …).

### What gets installed

| Goes to | Files | Purpose |
|---|---|---|
| `~/.claude/commands/` | `workflow.md`, `wf.md`, `sweep.md`, `gardener.md`, `research.md`, `r.md`, `think.md`, `reflect.md`, `tl.md` | the slash commands |
| `~/.claude/agents/` | `simplicity-cop.md`, `coherence-cop.md`, `coverage-cop.md`, `metrics-cop.md`, … | reviewer sub-agents `/wf` spawns |
| `~/.claude/reference/` | `code-quality-metrics.md` | metrics-cop threshold source-of-truth |
| `~/.claude/statusline.sh` | `statusline.sh` | optional status bar (model · cwd · branch · context%); needs a `statusLine` key in `settings.json` |
| `~/.claude/hooks/enforce_codex_mcp_policy.py` | `.claude/hooks/enforce_codex_mcp_policy.py` | forces non-interactive policy on nested Codex MCP calls |
| `~/.claude/skills/cc/` | `.claude/skills/cc/SKILL.md` | standalone `/cc` Claude-orchestrated, Codex-coded workflow |
| `~/.claude/skills/manager/` | `.claude/skills/manager/SKILL.md` | explicit-only cmux team lead above isolated `/cc` tracks |
| `~/.claude/skills/in-browser-verify/` | `SKILL.md`, `scripts/`, `assets/` | web-app scenario ledger + browser-proof done-gate |

`~/.claude/` = available in every project. A project's `.claude/` = that repo only, and it wins when both define the same name. `/wf` and `/gardener` write per-project longitudinal ledgers (`ratchet.tsv`, `debt.tsv`) into the project's `.claude/metrics/` — those stay in the project, not global.

Settings (`MCP_TIMEOUT`/`MCP_TOOL_TIMEOUT`, the allowed MCP tools, etc.) are not shipped — `settings.local.json` is gitignored. Tell the installer to add only what you want into your own `~/.claude/settings.json`.

**One live tree for host + VM:** `bash scripts/link-globals.sh link` symlinks the global commands, agents, skills, bridge scripts and hook into this checkout (`status` checks). Claude Code and Codex share one lean rules file, gitignored `global/AGENTS.md`; `/reflect` and `$reflect` write full incidents to `global/log/` and at most one line to that file (see `global/README.md`).

The base workflows run with **no MCP at all** — the optional reviewers just downgrade and say so. The MCP setup below is opt-in.

## MCP setup (optional for base workflows; required for `/cc`)

External agent roles use **local stdio** MCP servers — commands on your machine, not remote URLs.

**Codex reviewer (`-c` in `/wf`) and `/cc` coder** — the official Codex CLI's built-in MCP server:

```
claude mcp add --transport stdio --scope user codex-cli -- codex mcp-server
claude mcp add-json --scope user codex-coder '{"type":"stdio","command":"codex","args":["mcp-server"],"timeout":1800000}'
```

`/cc` requires both servers. `codex-coder` has the 30-minute timeout used by writable coding calls; this repo's `.mcp.json` supplies it locally. Restart Claude Code after adding or approving it. Both need the `codex` CLI installed and logged in; no API key goes into MCP config.

Codex MCP has a per-call `approval-policy`; a server-process override does not
replace its `on-request` call default. To prevent nested approval prompts from
waiting forever, install `.claude/hooks/enforce_codex_mcp_policy.py` under
`~/.claude/hooks/` and add a user-level `PreToolUse` hook in
`~/.claude/settings.json` for `mcp__codex-cli__codex` (and
`mcp__codex-coder__codex` if installed). The hook preserves the caller's full
input and sandbox while forcing `"approval-policy": "never"`.

**Antigravity reviewer (`-g`, opt-in)** — the repository-owned `codex/bin/agy-peer-mcp` bridge. It asks Antigravity first and routes to the configured local Gemini-compatible fallback only when Antigravity is unavailable:

```
claude mcp add --transport stdio --scope user agy -- "$(pwd)/codex/bin/agy-peer-mcp"
codex mcp add agy -- "$(pwd)/codex/bin/agy-peer-mcp"
mkdir -p "$HOME/.local/bin"
ln -sf "$(pwd)/codex/bin/agy-peer-mcp" "$HOME/.local/bin/agy-ask"
```

The MCP and `agy-ask` command are two transports into the same router. Agents use the command only when an existing session did not load the MCP; they never choose the provider. The default fallback is `http://127.0.0.1:8300`, model `gemini-3.5-flash`. Override it with `AGY_FALLBACK_BASE_URL` and `AGY_FALLBACK_MODEL`. Restart the MCP hosts after registration or bridge updates.

Routing policy belongs to this Orchestrator repository because its workflows decide when and how an independent reviewer participates. The fallback service (currently `google300`) remains a narrow Gemini-compatible Vertex facade: it owns Vertex authentication, model availability, and spend metering, but knows nothing about AGY or MCP. If both routes fail, the bridge returns an MCP/JSON-RPC error so workflows record the reviewer as unreachable instead of accepting an error message as a review.

Security checklist for any MCP server:

- **Local stdio over remote.** Prefer a command you can audit; be wary of remote MCP URLs.
- **No secrets in config.** Don't paste API keys/tokens into the MCP entry — use the tool's own login (Codex) or environment variables.
- **Credentials stay out of the repo.** Any service-account key lives outside the working tree, `chmod 600`, never committed (this repo keeps key paths out of the tree and scrubs them from docs for that reason).
- **Least privilege.** Scope a cloud service account to exactly the API it needs — never Owner/Editor.
- **Read before you add, scope per user.** Review a server's source and deps first. Use `--scope user` for personal servers so a project-level `.mcp.json` never ships your machine paths.

Missing MCP is fine — `/wf` continues with the reviewer downgraded (pass `--abort-on-missing-mcp` if you'd rather it hard-fail).
`/cc` is strict: missing Codex reviewer/coder tools or a failed coding call hard-stops and never falls back to a Claude coder.
`/manager` additionally requires `/cc` plus a Claude session launched by `cmux claude-teams`; each repository needs `/manager --smoke-test` for the current Claude/cmux/Codex/skill fingerprint before production fan-out.

## Commands

| Command | What it does |
|---|---|
| `/workflow` (`/wf`) | The workflow. Tier-auto TDD on modern primitives. Intake infers obvious defaults instead of asking (`Assumptions` block to override). Codex reviewer on by default (`--no-codex` to skip). Prints `workflow v0.29 (19-jun-2026)` as its first line. |
| `/cc` | Standalone Claude-led workflow: Codex authors plan/tests/code/fixes and runs cops; Claude reviews both gates — the plan (Gate 1) and the code (Gate 2, fresh agent). |
| `/manager` | Explicit-only cmux orchestrator with `--plan-only` and a required `--smoke-test` before isolated `/cc` fan-out. |
| `/gardener` | Periodic entropy removal. Reads the longitudinal ledgers (`.claude/metrics/ratchet.tsv`, `debt.tsv`), sweeps for duplication / dead code, and executes the top-K cleanups as small `/wf`-style tasks (`--top=K`, `--dry-run`). |
| `/sweep` | End-of-session working-tree sweep. Classifies each uncommitted path (discard/ignore/commit-main/commit-sidecar/stash/hold) and executes so `git status` ends clean. Codex on by default (`--fast` / `--no-codex` to skip); secrets hard-fenced from auto-commit; never pushes. Prints `sweep (19-jun-2026)` as its first line. |
| `/research` (`/r`) | Single-agent Claude codebase/web research by default. `-c` adds one bounded Codex pass, `-g` adds one bounded agy pass, and `--multi-agent` explicitly permits Explore fan-out. Artifact in `.claude/research/`. |
| `$research` (Codex skill) | Codex-led equivalent with evidence adjudication. A bounded peer call from a parent research workflow returns inline without recursively spawning another research run. Artifact in `codex/research/` for standalone runs. |
| `/think` | Claude-chaired Claude + Codex + Gemini council with independent first passes, peer review, and default adversarial cross-examination. |
| `$think` (Codex skill) | Codex-chaired Codex + Claude + Gemini council with independent first passes, peer review, and default adversarial cross-examination. |
| `/reflect` | Turn recurring failures into rules. |
| `$reflect` (Codex skill) | On confirmed mistakes/corrections: postmortem, recurrence check, permanent `AGENTS.md` rule, and L1→L4 escalation. |
| `/tl` | Tweet-size summary of the last output + clickable next-action buttons. |
| `$tldr` (Codex skill) | Single-line `$tldr — <summary>` of the last output + concrete next-action choices. |
| `in-browser-verify` (skill) | Per-repo web verification: durable `verification/scenarios.md` ledger, scenario→Playwright ID mapping, full-suite gate with fresh trace evidence, and a Stop hook that blocks "done" without a passed manifest. Onboard a web repo with `init`; hooks stay project-local. |

### Loop skills (local, experimental — under test)

Five distinct agentic-loop best-practices as project-local skills (`.claude/skills/`, `22-jun-2026`), grounded in Karpathy / Boris Cherny / Reflexion / Ralph. Invoke each by name to A/B them:

| Skill | Loop | Stop condition |
|---|---|---|
| `goal-act-verify` | minimal goal→act→verify | deterministic check passes |
| `leashed-autonomy` | Karpathy autonomy slider (L1–5) + blast radius | goal met, budget hit, or boundary needs approval |
| `reflexion-repair` | cited self-critique for debug/test repair | green, or same hypothesis fails 2× |
| `evaluator-optimizer` | best-of-N, rubric written first | top score ≥ threshold or plateau |
| `ralph-loop` | fresh-context brute-force, git = memory | checklist clean, cap, or 2 no-progress passes |

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
│       ├── think/
│       ├── reflect/
│       ├── tldr/
│       └── in-browser-verify/
├── bin/
├── postmortems/
├── research/
└── temp/        # gitignored scratch
```

Fresh clone: link these skills into Codex's global discovery path from the repository root (plain `ln` refuses to replace an existing target):

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD/codex/.agents/skills/research" "$HOME/.agents/skills/research"
ln -s "$PWD/codex/.agents/skills/think" "$HOME/.agents/skills/think"
```

Invoke them in Codex as `$wf <task>`, `$research <topic>`, `$think <topic>`, `$reflect`, `$tldr`, and `$in-browser-verify`, or choose them from `/skills`. `$research` owns independent multi-model evidence gathering and source adjudication; `$think` owns deliberation, peer critique, and default cross-examination. Neither skill exposes a debate flag. `$reflect` is implicit on confirmed mistakes/user corrections; `python3 codex/.agents/skills/reflect/scripts/reflection.py install` makes it globally discoverable and installs the durable reflection contract in `~/.codex/AGENTS.md`. `$wf` stays explicit-only; ordinary code requests use Codex directly under the applicable `AGENTS.md` verification rules. `$in-browser-verify` is standalone: its installer makes only the skill globally discoverable; `init` adds `SessionStart`/`Stop` hooks locally to each explicitly onboarded web repository along with the tracked scenario and command contract. Non-web repositories load no verification hooks. Start a new Codex session if skills do not appear immediately, and review new project hooks in `/hooks`. Codex custom prompt slash commands exist as `/prompts:<name>`, but they are user-local under `~/.codex/prompts` and deprecated, so this repo uses skills instead.

Older generations are archived in [legacy/](legacy/) (outside `.claude/` so Claude Code doesn't auto-register them as commands). They're kept in the repo as evolutionary context for AI coders reading the codebase, not for invocation.

## Why bother

Vanilla Claude reviews its own work and the review is biased. `/wf` enforces three things vanilla skips: TDD as a gate (RED then GREEN, both verified), zero-context reviewers (no planning history → can't be optimistic), and `EXECUTION_BLOCK` proof (command + output + exit code) before any completion claim. Plus `BASELINE_BLOCK`/`REGRESSION_DELTA` anti-regression, and portable safety/verification rules every in-repo session inherits (authorization gates, no-clobber, live-over-docs). Full set in [CLAUDE.md](CLAUDE.md) (Codex reads them via [AGENTS.md](AGENTS.md)).

## Optional reviewers

- `-c` means "the other main model": Claude commands call Codex; Codex skills call Claude.
- `-g` means Gemini / Antigravity through the agy bridge MCP (`mcp__agy__agy_ask`).

Codex `-c` uses the official-Claude bridge at `~/.agents/bin/claude-peer` or `codex/bin/claude-peer`, preferring the user-local copy. It requires Claude Code subscription login (`claude.ai`) and refuses API-key auth, so it uses your Claude quota, not API billing. This is for local personal workflow use; workflows must say clearly when an optional reviewer is unavailable.

The repository-owned agy bridge owns model selection and routing. It uses Antigravity first, then auto-routes to its configured local fallback and prefixes every response with the actual route. Credentials remain inside the fallback service; they are never placed in MCP configuration. Workflows should treat that as the intended Gemini fallback, not substitute Claude/Codex or inline self-review. Restart the MCP host after bridge-code updates.

## Thanks

A GitHub star on [lebed2045/orchestration](https://github.com/lebed2045/orchestration) tells me what's worth building more of. PRs welcome. "This didn't work for me" reports are most valuable.

## License

MIT
