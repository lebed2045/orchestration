# 02-auth-system-sub1: Foundation - Project & User Model

## Goal
Working TypeScript project with Prisma schema, User model, and RefreshToken model.

## Requirements
- Initialize npm project with TypeScript
- Install dependencies: express, bcrypt, jsonwebtoken, prisma, @prisma/client
- Install dev deps: typescript, ts-node, @types/*, jest, ts-jest, supertest
- Create tsconfig.json with strict mode
- Create Prisma schema with:
  - User model: id, email (unique + validation), passwordHash, createdAt
  - RefreshToken model: id, token, userId, expiresAt, createdAt
- Run prisma generate to create client
- Basic test: can connect to SQLite and create/read a user

## Technical
- Use SQLite for database (file: ./dev.db)
- Email validation: must contain @
- Structure: src/ folder for source code

## Parent
Card: .claude/pm/02-auth-system.md
Subtask: 1 of 3

## Test
1. `npm install` completes without errors
2. `npx prisma generate` succeeds
3. TypeScript compiles without errors
4. Basic DB test passes (create user, read user)

## Produces (for Sub2)
- package.json with all dependencies
- tsconfig.json
- prisma/schema.prisma
- node_modules/@prisma/client (generated)
- src/ folder structure
