# Phase 1 — Foundation + JWT Auth

## Objective
Stand up the monorepo, connect the backend to MongoDB, and ship working
register / login / protected-dashboard flows end to end.

## What was built
**Backend (`backend/app`)**
- `core/config.py` — env-driven settings (Mongo URI, JWT secret, CORS origins)
- `core/database.py` — shared async Motor client + `ensure_indexes()` (unique `users.email`)
- `core/security.py` — bcrypt password hashing, JWT access/refresh token encode+decode
- `models/user.py` — `users` Mongo document shape (matches §6 of Phase 0 plan)
- `schemas/auth.py`, `schemas/common.py` — request/response schemas, `{success,data,error}` envelope
- `services/auth_service.py` — register/login/get-current-user business logic
- `api/deps.py` — bearer-token dependency + `require_admin` (ready for Phase 12)
- `api/routes/auth.py` — `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `main.py` — FastAPI app, CORS, startup index creation, `GET /api/health`

**Frontend (`frontend/src`)**
- `api/axios.js` — shared Axios instance, attaches JWT, redirects to `/login` on 401
- `context/AuthContext.jsx` — login/register/logout + current-user state
- `components/ProtectedRoute.jsx`, `components/Navbar.jsx`
- `pages/Login.jsx`, `pages/Register.jsx`, `pages/Dashboard.jsx`
- `App.jsx` / `main.jsx` — routing, `/dashboard` gated behind `ProtectedRoute`

## How to verify
1. `cp .env.example .env`, fill in a real `MONGO_URI` (Atlas free tier) and a random `JWT_SECRET_KEY`.
2. `docker-compose up --build` (or run backend/frontend separately — see README).
3. Visit `http://localhost:5173/register`, create an account.
4. Log in — you should land on `/dashboard` and see your email.
5. `GET http://localhost:8000/docs` — confirm `/api/auth/register`, `/api/auth/login`,
   `/api/auth/me` are listed with the `{success,data,error}` envelope.
6. Hit `/dashboard` directly while logged out — should redirect to `/login`.

## Known gaps (intentional, deferred to later phases)
- No refresh-token rotation endpoint yet (access token just expires; re-login for now)
- No onboarding form (interests/budget/style) — that's part of Phase 2
- No rate limiting / password-reset flow — bundled into Phase 13 (security hardening)

## Next phase
**Phase 2 — Destination & place browsing + admin CRUD**: `destinations` and
`tourist_places` collections, `GET /api/destinations`, `GET /api/places` with
filters, and admin-only CRUD on places (using `require_admin` from `api/deps.py`).

Say **"start phase 2"** to continue.
