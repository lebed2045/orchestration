# Specification: [Feature Name]

## Overview

[1-2 sentence summary of what this feature does]

## Functional Requirements

- FR1: [The system shall...]
- FR2: [The system shall...]
- FR3: [The system shall...]

## Inputs

| Input | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| input1 | string | Yes | non-empty | Description |
| input2 | number | No | >= 0 | Description |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| result | object | The main result |
| error | Error | When something fails |

## Edge Cases

| ID | Scenario | Input | Expected Behavior |
|----|----------|-------|-------------------|
| EC1 | Empty input | "" | Return error |
| EC2 | Very large input | 10MB | Handle gracefully |
| EC3 | Special characters | "<script>" | Escape properly |

## Error Handling

| Error Code | Condition | Response |
|------------|-----------|----------|
| ERR_INVALID_INPUT | Input validation fails | Return 400 with message |
| ERR_NOT_FOUND | Resource doesn't exist | Return 404 |
| ERR_INTERNAL | Unexpected error | Return 500, log details |

## Constraints

- Performance: Response within 200ms
- Security: No PII in logs
- Compatibility: Node 18+
- Dependencies: Minimize external deps

## Success Criteria

- [ ] All functional requirements implemented
- [ ] All edge cases handled
- [ ] All tests passing
- [ ] No security vulnerabilities
- [ ] Documentation updated

## Out of Scope

- [Feature X is not included in this iteration]
- [Integration with Y is deferred]

## Examples

### Example 1: Happy Path

**Input:**
```json
{
  "input1": "hello",
  "input2": 42
}
```

**Output:**
```json
{
  "result": "processed hello with 42"
}
```

### Example 2: Error Case

**Input:**
```json
{
  "input1": ""
}
```

**Output:**
```json
{
  "error": "input1 cannot be empty"
}
```

## Notes

- [Any additional context]
- [Technical considerations]
- [Dependencies on other features]
