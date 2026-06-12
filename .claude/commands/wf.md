---
description: "Short alias for /workflow. TDD workflow - invoke ONLY when the user explicitly types /wf or /workflow; never auto-route code changes here. Codex MCP review runs by DEFAULT on every tier; --no-codex opts out."
argument-hint: "[flags] <task>"
---

# /wf — short for /workflow

Invoke the `workflow` skill (Skill tool — not the built-in Workflow orchestration tool) with the arguments below passed through verbatim. Follow only the skill file. Tell it you were invoked via the `/wf` wrapper so its second-line help banner uses the `/wf — short for /workflow: …` variant; its first-line version banner prints as usual.

$ARGUMENTS
