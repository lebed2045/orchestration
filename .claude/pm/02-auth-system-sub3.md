# 02-auth-system-sub3: Integration - Middleware & Full Tests

## Goal
Session middleware for protected routes and all 6 test cases from parent card passing.

## Requirements
- Auth middleware that:
  - Extracts Bearer token from Authorization header
  - Verifies JWT and attaches user to request
  - Returns 401 if no token or invalid token
- Protected route example: GET /protected (returns user info)
- All 6 tests from parent card:
  1. Register user with email/password
  2. Login with credentials -> receive JWT
  3. Access protected route with token -> 200
  4. Access protected route without token -> 401
  5. Logout -> token invalidated
  6. Use old token -> 401 (refresh token invalidated)

## Technical
- Middleware checks Authorization: Bearer <token>
- Use jwt.utils.ts verifyToken function
- Add register endpoint if needed for tests

## Parent
Card: .claude/pm/02-auth-system.md
Subtask: 3 of 3

## Requires (from Sub2)
- Working /auth/login and /auth/logout endpoints
- JWT utilities (generateAccessToken, verifyToken)
- Express app running

## Test
All 6 tests from parent card must pass:
1. Register user with email/password - PASS
2. Login with credentials -> receive JWT - PASS
3. Access protected route with token -> 200 - PASS
4. Access protected route without token -> 401 - PASS
5. Logout -> token invalidated - PASS
6. Use old refresh token -> 401 - PASS

## Produces (Final)
- src/auth/auth.middleware.ts
- Protected route at GET /protected
- tests/auth.test.ts with all 6 tests
- All tests passing
