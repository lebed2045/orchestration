# 02: Add auth system

## Goal
User login/logout with session persistence.

## Requirements
- Password hashing with bcrypt
- JWT token generation
- Login endpoint `POST /auth/login`
- Logout endpoint `POST /auth/logout`
- Session middleware for protected routes
- User model with email/password

## Technical
- Use bcrypt for password hashing
- Use jsonwebtoken for JWT
- Store refresh tokens in database
- Access token expires in 15min
- Refresh token expires in 7 days

## Test
1. Register user with email/password
2. Login with credentials → receive JWT
3. Access protected route with token → 200
4. Access protected route without token → 401
5. Logout → token invalidated
6. Use old token → 401

---

## Execution Log

| Run | Date | Status | Artifacts |
|-----|------|--------|-----------|
| 1 | 2026-01-27 | SUCCESS | auth-system/ (19 files) |

### How to Verify

```bash
cd auth-system && npm test
```

### Reflection

- Decomposed into 3 subtasks due to LOC estimate (280 > 50 threshold)
- Sub2 overdelivered, completing Sub3 requirements early
- All 6 test cases pass
- Gemini noted: `src/index.ts` is stub (tests work, but not runnable standalone)
