# Orchestration Mode Visualization

```text
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  [Orc.PhaseX_NAME] [Gemini: Y/3] [Status: in_progress|waiting|complete]           ║
║                        ORCHESTRATION MODE VISUALIZATION                           ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  PHASE FLOW                              MCP TOOL CALL TREE                       ║
║  ══════════                              ══════════════════                       ║
║                                                                                   ║
║  ╔═══════════════════════════════╗       @orchestrate                             ║
║  ║      PLAN MODE SANDBOX        ║       │                                        ║
║  ║  ┌─────────────────────────┐  ║       ├── EnterPlanMode ◄────────────────────┐ ║
║  ║  │ Orc.Phase1_INTAKE       │  ║       │   │                                  │ ║
║  ║  │ → artifacts/spec.md     │──╫──────►│   ├── AskUserQuestion                │ ║
║  ║  │ [■■■■■■■■■■] ✓          │  ║       │   ├── Task(intake)                   │ ║
║  ║  └───────────┬─────────────┘  ║       │   │   ├── Read                       │ ║
║  ║              │                ║       │   │   ├── Glob                  PLAN │ ║
║  ║              ▼                ║       │   │   └── Write                 MODE │ ║
║  ║  ┌─────────────────────────┐  ║       │   │                                  │ ║
║  ║  │ Orc.Phase2_PLANNING     │  ║       │   ├── Task(planner)                  │ ║
║  ║  │ → architecture.md       │──╫──────►│   │   ├── Read                       │ ║
║  ║  │ [■■■■■■■■■■] ✓          │  ║       │   │   ├── Grep                       │ ║
║  ║  └───────────┬─────────────┘  ║       │   │   └── Write                      │ ║
║  ║              │                ║       │   │                                  │ ║
║  ║              ▼                ║       │   └── mcp__gemini__ask-gemini        │ ║
║  ║  ┌─────────────────────────┐  ║       │       │                              │ ║
║  ║  │ Orc.Phase3_GEMINI_REVIEW│  ║       │       ├─► Gemini: 1/3 NEEDS_WORK ────┘ ║
║  ║  │ [■■■■■■░░░░] Gemini:1/3 │──╫──────►│       │   (iterate up to 3x)           ║
║  ║  └───────────┬─────────────┘  ║       │       └─► Gemini: 2/3 ✓ APPROVED       ║
║  ║              │                ║       │                                        ║
║  ╚══════════════╪════════════════╝       ├── ExitPlanMode                         ║
║                 ▼                        │                                        ║
║  ┌─────────────────────────────┐         │                                        ║
║  │ Orc.Phase4_USER_GATE        │◄─STOP──►│   [User reviews plan]                  ║
║  │ [waiting for approval]      │         │                                        ║
║  └───────────┬─────────────────┘         │                                        ║
║              │ ✓ approved                │                                        ║
║              ▼                           ├── Task(coder)                          ║
║  ┌─────────────────────────────┐         │   │                                    ║
║  │ Orc.Phase5_TDD              │         │   │  RED PHASE (tests fail)            ║
║  │ RED ✗ → GREEN ✓             │─────────│   ├── Write → test.spec.ts             ║
║  │ [■■■■■■■■░░]                │         │   ├── Bash → npm test (FAIL ✗)         ║
║  └───────────┬─────────────────┘         │   │                                    ║
║              │                           │   │  GREEN PHASE (tests pass)          ║
║              │                           │   ├── Write → implementation.ts        ║
║              │                           │   └── Bash → npm test (PASS ✓)         ║
║              ▼                           │                                        ║
║  ┌─────────────────────────────┐         │  ┌─────────────┬─────────────┐         ║
║  │ Orc.Phase6_DUAL_REVIEW      │         │  │             │             │         ║
║  │ → review-feedback.md        │─────────┤  ▼             ▼             │         ║
║  │ [■■■■■■■■■░]                │         │  Gemini    Fresh Claude      │         ║
║  └───────────┬─────────────────┘         │  Review    (Bash spawn)      │         ║
║              │                           │  │             │             │         ║
║              │ ◄─────────────────────────┘  └──────┬──────┘             │         ║
║              │                                     │ merge              │         ║
║              ▼                                     ▼                    │         ║
║  ┌─────────────────────────────┐         [Aggregate Review Feedback]    │         ║
║  │ Orc.Phase7_USER_GATE_CODE   │◄─STOP───────────────────────────────►─┘         ║
║  │ [waiting for approval]      │                                                  ║
║  └───────────┬─────────────────┘                                                  ║
║              │ ✓ approved                                                         ║
║              ▼                                                                    ║
║  ┌─────────────────────────────┐                                                  ║
║  │ Orc.Phase8_SUMMARY          │         Output: ✓ ORCHESTRATION COMPLETE          ║
║  │ ✓ ORCHESTRATION COMPLETE    │                                                  ║
║  └─────────────────────────────┘                                                  ║
║                                                                                   ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║  ARTIFACTS                          │  AGENTS                                     ║
║  ─────────                          │  ──────                                     ║
║  Phase1 → artifacts/spec.md         │  intake   (sonnet) → requirements           ║
║  Phase2 → artifacts/architecture.md │  planner  (opus)   → design                 ║
║  Phase6 → artifacts/review-feedback.md  coder   (sonnet) → TDD                    ║
║                                     │  reviewer (sonnet) → isolated review        ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
```

## Legend

| Symbol | Meaning |
|--------|---------|
| `╔═══╗` | Double-line box: Major boundary (Plan Mode Sandbox) |
| `┌───┐` | Single-line box: Phase container |
| `──►`  | Flow/connection to tool call |
| `◄──`  | Feedback loop / iteration |
| `STOP` | User gate - execution pauses |
| `[■■░░]` | Progress indicator |
| `✓`    | Completed/approved |
| `✗`    | Failed (expected in RED phase) |

## State Header Format

Every orchestration response starts with:

```
[Orc.PhaseX_NAME] [Gemini: Y/3] [Status: in_progress|waiting|complete]
```

- **PhaseX_NAME**: Current phase (e.g., `Phase1_INTAKE`)
- **Gemini: Y/3**: Review iteration count (max 3)
- **Status**: Current state of the phase

## Key Concepts

### Plan Mode Sandbox (Phases 1-3)
Phases 1-3 execute inside Claude's built-in Plan Mode:
- Read-only exploration
- No code changes
- Gemini reviews before exiting

### User Gates (Phases 4 & 7)
Two mandatory approval points:
1. **Phase 4**: Plan approval before coding
2. **Phase 7**: Code approval before completion

### TDD Cycle (Phase 5)
Strict test-driven development:
1. **RED**: Write tests that fail
2. **GREEN**: Write minimal code to pass
3. Repeat until complete

### Dual Review (Phase 6)
Two independent reviewers:
1. **Gemini MCP**: External AI review
2. **Fresh Claude**: Isolated instance via `claude -p`
