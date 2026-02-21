# Research: Industry Best Practices for AI Reflection & Failure Tracking

Generated: 2026-02-21 22:25
Agents: Opus + Gemini + Codex
Focus: **What top coders actually do** (not theory)

---

## Executive Summary

Top practitioners treat **mistakes as institutional data**. The pattern: mistake observed → rule added to CLAUDE.md → team learns. Boris Cherny's team updates CLAUDE.md "multiple times per week" from PR review learnings. Simon Willison publishes full session transcripts for auditability. The emerging standard is **versioned instruction files as code**, not static prompts.

---

## Named Practitioners & Their Systems

### Boris Cherny (Creator of Claude Code, Anthropic)

**Source**: [Twitter thread](https://twitter-thread.com/t/2007179832300581177), [VentureBeat](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are)

| Practice | Implementation |
|----------|----------------|
| **Mistake → Rule loop** | "Every mistake becomes a rule" in CLAUDE.md |
| **Frequency** | CLAUDE.md updated multiple times per week |
| **PR integration** | Uses `@.claude` tag on coworker PRs to add learnings |
| **Plan-first** | Goes back and forth in Plan Mode until plan is solid |
| **Parallelism** | Runs 5+ concurrent Claude instances across worktrees |
| **Slash commands** | `/commit-push-pr` invoked dozens of times daily |

**Key quote**: "Each team at Anthropic maintains a CLAUDE.md in git to document mistakes, so Claude can improve over time."

### Simon Willison (Developer, AI Tooling Expert)

**Sources**:
- [claude-code-transcripts repo](https://github.com/simonw/claude-code-transcripts)
- [CLAUDE.md](https://raw.githubusercontent.com/simonw/claude-code-transcripts/main/CLAUDE.md)
- [AGENTS.md](https://raw.githubusercontent.com/simonw/claude-code-transcripts/main/AGENTS.md)
- [Blog post](https://simonwillison.net/2025/Dec/25/claude-code-transcripts/)

| Practice | Implementation |
|----------|----------------|
| **Session transcripts** | Archives Claude sessions as reviewable HTML |
| **notes.md logging** | Required running log per research task |
| **CLAUDE.md → AGENTS.md** | Single-line indirection pattern |
| **Commit scoping** | Only commit new outputs/diffs (forces reflection) |
| **TDD requirement** | Encoded in AGENTS.md as mandatory |

**His AGENTS.md pattern** (from simonw/research):
```markdown
- Create folder for each task
- Maintain notes.md as continuous log
- Write final README.md report
- Commit only outputs, not intermediate attempts
```

### Addy Osmani (Google Chrome Team)

**Source**: [AI Coding Workflow 2026](https://addyosmani.com/blog/ai-coding-workflow/)

| Practice | Implementation |
|----------|----------------|
| **Brainstorm first** | Detailed spec with AI before any code |
| **Extra scrutiny** | AI code needs MORE review, not less |
| **Step-by-step plans** | Outline plan before implementation |

**Key insight**: "The key is to not skip the review just because an AI wrote the code."

---

## Real File Examples (Public Repos)

### Simon Willison's CLAUDE.md

```markdown
# From: simonw/claude-code-transcripts/CLAUDE.md
@AGENTS.md
```
(Single-line pointer to canonical file)

### Simon Willison's AGENTS.md

```markdown
# From: simonw/research/AGENTS.md
- Create a folder for each task
- Maintain a notes.md file with running log
- Final output: README.md report
- Commit only final artifacts
- Run tests before claiming done
```

### OpenAI's AGENTS.md

**Source**: [openai-agents-js/AGENTS.md](https://raw.githubusercontent.com/openai/openai-agents-js/main/AGENTS.md)

```markdown
- Required validation steps before completion
- Commit/changeset rules
- Verification gates encoded
```

### Apache Airflow's AGENTS.md

**Source**: [airflow/AGENTS.md](https://raw.githubusercontent.com/apache/airflow/main/AGENTS.md)

```markdown
- Agent contributor checklist
- Points to setup/lint/test/PR docs
- Concise, not verbose
```

---

## Community Resources

| Resource | URL | Description |
|----------|-----|-------------|
| **awesome-cursorrules** | [GitHub](https://github.com/PatrickJS/awesome-cursorrules) | Curated .cursorrules examples |
| **AGENTS.md standard** | [GitHub](https://github.com/agentsmd/agents.md) | Cross-tool standardization |
| **Claude Code memory docs** | [Anthropic](https://docs.claude.com/en/docs/claude-code/memory) | Official memory hierarchy |
| **kinopeee/cursorrules** | [GitHub](https://github.com/kinopeee/cursorrules) | High-usage project rules |

---

## Failure Tracking Patterns (How Experts Do It)

### Pattern 1: Boris/Anthropic Team Loop

```
PR Review → Mistake observed → @.claude tag → CLAUDE.md updated → Team learns
```

- Happens during normal PR review workflow
- Not a separate "reflection" process
- Immediate addition to shared rules

### Pattern 2: Simon Willison's Transcript Archives

```
Session runs → Full transcript saved → HTML conversion → Public archive
```

- Enables forensic analysis of what went wrong
- Shareable for team learning
- Forces accountability

### Pattern 3: notes.md Running Log

```
Task starts → notes.md created → Continuous logging → Final report → Commit
```

- From Simon's research repo pattern
- Forces explicit reflection trail
- Only final artifacts committed

### Pattern 4: Verification Gates in Instructions

```markdown
# Example from industry AGENTS.md files
Before claiming "done":
1. Run tests: `npm test`
2. Run lint: `npm run lint`
3. Check for warnings
4. Provide execution output
```

---

## Emerging Standards (Industry Consensus)

| Standard | Description | Adoption |
|----------|-------------|----------|
| **Instructions as code** | Version-controlled, not static prompts | High |
| **Mistake → rule** | Failures become permanent rules | High |
| **Session transcripts** | Archive sessions for auditability | Growing |
| **Multi-layer memory** | Org → Project → Personal → Path | Emerging |
| **AGENTS.md unification** | Single standard across tools | Emerging |
| **Verification gates** | "Done" requires execution proof | Standard |

---

## Key Differences from Your Current System

| Your System | Industry Practice |
|-------------|-------------------|
| Log to failures.md, then propose rule | **Immediately** add rule to CLAUDE.md during PR review |
| Separate reflection process | Reflection **embedded** in PR review workflow |
| failures.md as archive | Session transcripts as archive (not failure-specific) |
| Batch promotion | Continuous promotion (multiple times per week) |
| Formal log format | Simple rule additions (less ceremony) |

---

## Recommended Takeaways

### 1. Embed in PR Review (Boris Pattern)

Don't separate failure tracking from PR review. When reviewing code:
- Spot mistake → Add rule to CLAUDE.md in same PR
- Use tag like `@.claude` to mark learnings

### 2. Archive Sessions (Simon Pattern)

Keep full session transcripts, not just failures:
- More context than failure logs
- Enables replay/forensics
- Shareable for team learning

### 3. Keep Instructions Concise

From [HumanLayer blog](https://www.humanlayer.dev/blog/writing-a-good-claude-md):
- 150 lines max for CLAUDE.md
- LLMs follow ~150-200 instructions consistently
- Use file:line references, not code snippets

### 4. Single-Line Pointer Pattern

From Simon Willison:
```markdown
# CLAUDE.md
@AGENTS.md
```
- Keeps canonical rules in one place
- CLAUDE.md just points to it
- Works across tools

### 5. Verification Gates as Standard

From OpenAI/Airflow patterns:
```markdown
Before claiming done:
- [ ] Tests pass
- [ ] Lint passes
- [ ] Execution output provided
```

---

## Sources

### Named Practitioners
- [Boris Cherny Twitter thread](https://twitter-thread.com/t/2007179832300581177)
- [Boris Cherny - VentureBeat](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are)
- [InfoQ - Claude Code Creator Workflow](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)
- [Simon Willison - claude-code-transcripts](https://github.com/simonw/claude-code-transcripts)
- [Simon Willison blog](https://simonwillison.net/2025/Dec/25/claude-code-transcripts/)
- [Addy Osmani - AI Coding Workflow 2026](https://addyosmani.com/blog/ai-coding-workflow/)

### Real File Examples
- [simonw CLAUDE.md](https://raw.githubusercontent.com/simonw/claude-code-transcripts/main/CLAUDE.md)
- [simonw AGENTS.md](https://raw.githubusercontent.com/simonw/claude-code-transcripts/main/AGENTS.md)
- [simonw/research AGENTS.md](https://raw.githubusercontent.com/simonw/research/main/AGENTS.md)
- [openai-agents-js AGENTS.md](https://raw.githubusercontent.com/openai/openai-agents-js/main/AGENTS.md)
- [apache/airflow AGENTS.md](https://raw.githubusercontent.com/apache/airflow/main/AGENTS.md)

### Community Resources
- [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)
- [AGENTS.md standard](https://github.com/agentsmd/agents.md)
- [Claude Code memory docs](https://docs.claude.com/en/docs/claude-code/memory)
- [Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

### Agent Contributions
- **Opus**: Web search synthesis
- **Gemini**: Practitioner research, hierarchical patterns
- **Codex**: Real file examples, public repo analysis

---

**Artifact:**
`File: /Users/elpinguino/dev_local/orchestration/.claude/research/industry-reflection-practices.md`
