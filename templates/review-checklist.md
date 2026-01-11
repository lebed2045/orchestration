# Code Review Checklist

Use this checklist for both Gemini and Fresh Claude reviews.

## Code Quality

### Readability

- [ ] Code is easy to understand without comments
- [ ] Variable/function names are descriptive
- [ ] No magic numbers (use constants)
- [ ] Consistent formatting
- [ ] No overly complex expressions

### Structure

- [ ] Functions are small and focused (single responsibility)
- [ ] No deep nesting (max 3 levels)
- [ ] No duplicate code (DRY)
- [ ] Logical file organization
- [ ] Clear module boundaries

### Maintainability

- [ ] Easy to modify without breaking other parts
- [ ] No tight coupling between components
- [ ] Dependencies are injected, not hardcoded
- [ ] Configuration is externalized

## Security

### Input Handling

- [ ] All inputs are validated
- [ ] Input length limits enforced
- [ ] Special characters properly escaped
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities

### Data Protection

- [ ] No secrets in code (API keys, passwords)
- [ ] Sensitive data not logged
- [ ] Proper error messages (no stack traces to users)
- [ ] Authentication/authorization checked

### Dependencies

- [ ] No known vulnerable dependencies
- [ ] Dependencies are up to date
- [ ] Minimal dependency footprint

## Testing

### Coverage

- [ ] All public functions have tests
- [ ] Happy path tested
- [ ] Error paths tested
- [ ] Edge cases from spec tested
- [ ] Boundary conditions tested

### Quality

- [ ] Tests are independent
- [ ] Tests are deterministic (no flaky tests)
- [ ] Test names describe what's being tested
- [ ] Assertions are meaningful
- [ ] No testing implementation details

## Performance

### Efficiency

- [ ] No unnecessary loops
- [ ] No N+1 query patterns
- [ ] Appropriate data structures used
- [ ] Memory usage is reasonable

### Scalability

- [ ] Will this work at 10x scale?
- [ ] Are there bottlenecks?
- [ ] Database queries optimized?

## Error Handling

### Robustness

- [ ] All errors are caught
- [ ] Errors are logged appropriately
- [ ] User-friendly error messages
- [ ] No silent failures
- [ ] Graceful degradation

### Recovery

- [ ] Can recover from transient failures
- [ ] Retry logic where appropriate
- [ ] Timeouts configured

## TypeScript Specific

- [ ] Proper types (no `any` unless justified)
- [ ] Null/undefined handled
- [ ] Strict mode enabled
- [ ] No type assertions unless necessary

## Documentation

- [ ] Complex logic has comments
- [ ] Public API documented
- [ ] README updated if needed
- [ ] No outdated comments

---

## Review Output Format

```markdown
# Code Review: [Feature Name]

**Reviewer:** [Gemini/Fresh Claude]
**Date:** [Date]

## Summary
[Overall assessment: APPROVED / NEEDS_WORK]

## Critical Issues (Must Fix)
1. [Issue description]
   - Location: [file:line]
   - Impact: [what could go wrong]
   - Suggestion: [how to fix]

## Warnings (Should Fix)
1. [Issue description]
   - Location: [file:line]
   - Suggestion: [how to improve]

## Suggestions (Nice to Have)
1. [Suggestion]

## What's Good
- [Positive observation 1]
- [Positive observation 2]

## Checklist Results
- Code Quality: [X/Y passed]
- Security: [X/Y passed]
- Testing: [X/Y passed]
- Performance: [X/Y passed]
```
