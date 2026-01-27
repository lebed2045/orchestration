# 02-auth-system-sub2: Core Auth - JWT & Endpoints

## Goal
Working login/logout endpoints that issue and invalidate JWT tokens.

## Requirements
- JWT utilities: generateAccessToken, generateRefreshToken, verifyToken
- Access token expires in 15 minutes
- Refresh token expires in 7 days, stored in database
- Login endpoint POST /auth/login:
  - Accepts { email, password }
  - Validates credentials with bcrypt
  - Returns { accessToken, refreshToken }
- Logout endpoint POST /auth/logout:
  - Accepts { refreshToken }
  - Deletes refresh token from database
  - Returns { success: true }
- Express app with JSON body parsing
- Routes mounted at /auth

## Technical
- Use jsonwebtoken for JWT
- Use bcrypt.compare for password verification
- Store JWT_SECRET in environment or config
- Salt rounds: 10 for bcrypt

## Parent
Card: .claude/pm/02-auth-system.md
Subtask: 2 of 3

## Requires (from Sub1)
- package.json with dependencies installed
- Prisma client generated
- User and RefreshToken models

## Test
1. POST /auth/login with valid credentials returns 200 + tokens
2. POST /auth/login with invalid password returns 401
3. POST /auth/logout with valid token returns 200
4. Refresh token is deleted from DB after logout

## Produces (for Sub3)
- src/auth/jwt.utils.ts
- src/auth/auth.controller.ts
- src/auth/auth.routes.ts
- src/index.ts (Express app)
- Working /auth/login and /auth/logout endpoints
