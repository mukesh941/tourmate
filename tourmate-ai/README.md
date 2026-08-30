# TourMate AI — Monorepo

Phase-by-phase build. See `docs/` for a per-phase summary.

## Phase 1 (this phase)
- Repo scaffold (`frontend/`, `backend/app/{api,models,schemas,services,ml,core}`)
- FastAPI backend with JWT auth (register / login / me)
- MongoDB connection via Motor (async)
- React + Vite + Tailwind frontend with Login/Register + a JWT-protected Dashboard
- `.env.example` — copy to `.env` and fill in real values before running

## Run locally
```bash
cp .env.example .env   # fill in MONGO_URI, JWT_SECRET_KEY

# backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
npm run dev
```
Or `docker-compose up --build` from the repo root once `.env` is filled in.

## Next
Say "start phase 2" for destination/place browsing + admin CRUD.
