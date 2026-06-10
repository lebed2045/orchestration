# Research: Claude From Codex `-c` Flag, MCP, and ToS

Generated: 2026-06-10 15:39 WITA
Mode: codebase + external
Degradation: initial diagnosis had no Claude pass because the Codex session had no Claude MCP tool configured.

## Executive Summary

The previous repo state did not actually call Claude from Codex. The Codex skills defined `-c` as "request Claude only if a callable Claude tool is available"; otherwise the workflow continued with a degradation note. At diagnosis time, `claude` existed (`2.1.170`) and `codex` existed (`0.139.0`), but `~/.codex/config.toml` only configured `node_repl` as an MCP server. There was no configured Claude MCP exposed to Codex.

The conservative implementation is a tiny local bridge around the official Claude Code CLI, not a full nested editor agent. It passes bounded diff/context to `claude -p` and returns a text verdict. It gives Claude no tools and no edit permission by default.

The user requirement is subscription/quota only, not API price. Therefore this repo should not use `ANTHROPIC_API_KEY`, `--bare`, direct Anthropic API calls, or a third-party provider for this bridge. It should require official Claude.ai login via Claude Code and refuse API-key auth.

## Local Findings

- `AGENTS.md` states the convention: Claude commands use `-c` for Codex, Codex skills use `-c` for Claude.
- `codex/.agents/skills/wf/SKILL.md` previously said `-c` requests a Claude reviewer only if a callable Claude reviewer tool is actually available.
- `codex/.agents/skills/research/SKILL.md` previously said `-c` uses an available Claude tool, otherwise runs a degraded inline second pass.
- `~/.codex/config.toml` had no Claude MCP server. The only explicit MCP server was `node_repl`.

## How To Call Claude From Codex

Use the official Claude Code CLI non-interactive mode, with user-local bridge precedence:

```bash
codex/bin/codex-review-context | ~/.agents/bin/claude-peer --mode review --task-file codex/temp/wf/spec.md
```

The bridge internally calls:

```bash
claude --safe-mode -p "<bounded prompt>" --tools "" --permission-mode dontAsk --no-session-persistence
```

with common API-key and third-party-provider environment variables unset for the child process.

## ToS / Policy Read

Not legal advice. Practical read:

- Official `claude -p` is documented for non-interactive use, scripts, CI, stdin pipes, structured output, and build-script style review tasks.
- Anthropic's Claude Code legal/compliance page says Pro/Max limits assume ordinary individual usage of Claude Code and Agent SDK.
- The same page says developers building products or services that interact with Claude capabilities should use API-key authentication, and Anthropic does not permit third-party developers to offer Claude.ai login or route requests through Free/Pro/Max plan credentials on behalf of users.
- Anthropic Commercial Terms prohibit using the services to build competing products or services, train competing AI models, reverse engineer, or duplicate the services.
- Therefore:
  - Personal local `claude -p` review on your own repo: likely intended.
  - Productized bridge for other users through your Claude subscription: risky / not allowed.
  - Company or product workflow: use the correct Anthropic commercial/API route.
  - This repo bridge must stay local, personal, read-only, and no-API-key.

## Recommendation For This Repo

Use `codex/bin/claude-peer` as the only Codex `-c` bridge:

- Auth mode: require Claude Code `authMethod=claude.ai`.
- No API billing: unset Anthropic API-key variables and common Bedrock/Vertex provider variables; refuse non-Claude.ai auth.
- Permissions: default `--tools ""`, `--safe-mode`, no edits, no Bash.
- Precedence: prefer `$HOME/.agents/bin/claude-peer` over a repo-local copy to avoid executing a malicious bridge from an untrusted checkout.
- Task text: pass via `--task-file`, not inline shell interpolation.
- Inputs: task summary, `git diff`, relevant test output, file snippets only when needed.
- Outputs: Claude text plus a required final verdict line for review mode.

This gives cross-model review without pretending a Claude MCP exists, and without turning the workflow into a brittle nested-agent setup.

## Sources

- Anthropic Claude Code docs, "Run Claude Code programmatically": https://code.claude.com/docs/en/headless
- Anthropic Claude Code legal/compliance: https://code.claude.com/docs/en/legal-and-compliance
- Anthropic Claude Code MCP docs: https://code.claude.com/docs/en/mcp
- Anthropic Commercial Terms: https://www.anthropic.com/legal/commercial-terms
- OpenAI Codex CLI features, MCP support: https://developers.openai.com/codex/cli/features
- Addy Osmani, "The Code Agent Orchestra": https://addyosmani.com/blog/code-agent-orchestra/
- Peter Steinberger, "My Current AI Dev Workflow": https://steipete.me/posts/2025/optimal-ai-development-workflow
- `steipete/claude-code-mcp`: https://github.com/steipete/claude-code-mcp
