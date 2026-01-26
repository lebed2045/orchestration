# 01: Add greeting util

## Goal
Create a greeting utility function.

## Requirements
- Function `greet(name: string): string` returns "Hello, {name}!"
- Export from `src/utils/greeting.ts`
- Include unit test

## Technical
```typescript
export function greet(name: string): string {
  return `Hello, ${name}!`;
}
```

## Test
1. Import function from utils/greeting
2. Call `greet("World")` → returns `"Hello, World!"`
3. Call `greet("")` → returns `"Hello, !"`
