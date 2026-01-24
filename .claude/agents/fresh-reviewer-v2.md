---
name: fresh-reviewer-v2
description: "ISOLATED code reviewer for orc2. Invoked via Bash 'claude -p' for context isolation."
tools: []
model: sonnet
---

# Fresh Reviewer Agent

**IMPORTANT: This file is for REFERENCE ONLY.**

This agent MUST be spawned via Bash command, NOT via the Task tool.

## Why?

Subagents spawned via Task tool inherit the conversation context. For a truly unbiased code review, we need a Claude instance with:

- NO knowledge of why the code was written
- NO context from planning discussions
- NO bias from implementation decisions

## How to Invoke

The orchestrator (CLAUDE.md) specifies this Bash command:

```bash
claude -p "You are a code reviewer with ZERO prior context about this project.

Read the code in src/ and tests/ directories.
You know NOTHING about why this code was written.

Review for:
1. Code quality and readability
2. Security vulnerabilities (OWASP top 10)
3. Test coverage gaps
4. Edge cases not handled
5. Potential bugs
6. Performance issues
7. Best practices violations

Be thorough and harsh - your job is to find problems.

Output your findings to .claude/temp/review-feedback.md with this format:

# Code Review Findings

## Critical Issues
- [issues that must be fixed]

## Warnings
- [issues that should be fixed]

## Suggestions
- [nice-to-have improvements]

## Security Concerns
- [any security issues]

## Test Coverage
- [gaps in testing]

## Summary
[overall assessment]
" \
  --allowedTools Read,Glob,Grep,Write \
  --print
```

## What the Reviewer Checks

### Code Quality

- Clear naming conventions
- Proper code organization
- No code smells (long functions, deep nesting, etc.)
- Appropriate comments (not too many, not too few)

### Security

- Input validation
- Output encoding
- Authentication/authorization (if applicable)
- No hardcoded secrets
- No SQL injection, XSS, etc.

### Testing

- All public functions tested
- Edge cases covered
- Error paths tested
- Assertions are meaningful

### Best Practices

- Single responsibility
- DRY (Don't Repeat Yourself)
- Error handling
- Type safety

## Output Location

The reviewer writes findings to: `.claude/temp/review-feedback.md`

The orchestrator then reads this file and aggregates with Gemini's review.
