# Orchestration Workflow Failures Log

---

## 2026-02-20 12:05 | orchestration

**Context:** Designing suffix naming convention for workflows

**Failure:** Confusion about boris2 design intent

**What happened:**
- User expected boris2 to be an AUTOMATED optimization of Boris's workflow (0 human gates)
- boris2 (formerly wf10) was actually designed with 1 human gate (plan approval in Phase 2)
- I marked boris2 as `-h` (has human gate) in the rename table
- User challenged: "How the fuck does it have a minus h?"

**Root cause:**
- Design mismatch: boris2.md was created with a human gate for plan approval (lines 103, 156)
- This contradicts user's mental model that "boris2 = automated Boris"
- Either the file was designed wrong, or there was a miscommunication

**Evidence from boris2.md:**
```
Line 103: ## Phase Flow (10 Phases, 2 Gates, 1 Human Gate)
Line 156: **Gate condition: User approves plan (explicit or implicit).**
Line 669: | Human gates | 0 | 1 (plan approval) |
```

**Resolution needed:**
- Clarify user intent: Should boris2 be autonomous or keep the human gate?
- If autonomous: Remove plan approval gate, add auto-commit
- If keeping gate: Rename to boris2-h per convention

**Lesson:**
- Verify design assumptions BEFORE documenting/renaming
- User's mental model of what a workflow "should be" may differ from what was implemented
- Ask clarifying questions about intent when there's ambiguity

---

## 2026-02-20 12:10 | orchestration

**Context:** Continuing suffix naming convention design

**Failure:** Incorrectly marked boris1 as having no human interaction

**What happened:**
- I said boris1 should have NO suffix (implying 0 human gates)
- But Boris's ACTUAL original workflow involves human interaction:
  - "Plan Mode → Iterate with user → Execute → Verify → Commit"
  - "Go back and forth refining the plan"
  - He asks questions, gets user feedback
- This IS human interaction, so boris1 SHOULD have `-h` suffix

**Evidence from my own research (boris-cherny-claude-code-practices.md):**
```
- Iterate on the plan with Claude until it's solid
- Go back and forth refining the plan before any code is written
```

**Root cause:**
- I confused "no external reviewers (Gemini/Codex)" with "no human interaction"
- Boris's workflow has no MCP tools but DOES have human plan iteration
- Failed to apply my own research to the naming convention

**Correct naming:**
- `boris-h` or `boris1-h` = Boris's original (HAS human plan iteration)
- `boris2` = Our autonomous optimization (no human interaction)

**Lesson:**
- "Human gate" means ANY human interaction, not just formal approval gates
- Plan iteration with user = human interaction = needs `-h` suffix
- Re-read source material before making claims

---
