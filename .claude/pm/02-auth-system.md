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
