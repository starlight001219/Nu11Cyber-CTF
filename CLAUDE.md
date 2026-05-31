# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Is This

Nu11Cyber CTF Platform (Project A033) — a CTF (Capture The Flag) competition platform. Users register, browse challenges by category, submit flags, and gain points. Some challenges have dynamic Docker-based lab instances that users can deploy on demand.

## Tech Stack

- **Backend**: FastAPI (async), SQLAlchemy 2.0 (async), SQLite (dev), JWT auth (python-jose), AES-256-GCM flag encryption
- **Frontend**: Single vanilla HTML/JS file (no framework), matrix rain canvas animation
- **Infrastructure**: Docker Compose (backend + Redis + Nginx), Nginx reverse proxy serving static frontend + API proxy

## Project Structure

```
Nu11Cyber-CTF/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # FastAPI app factory, CORS, exception handlers, route registration
│   │   ├── config.py             # Settings via pydantic-settings (reads .env)
│   │   ├── database.py           # SQLAlchemy async engine + session
│   │   ├── models.py             # ORM models: User, Challenge, Solve, LabInstance, Submission
│   │   ├── crypto.py             # Password/flag encryption (AES-GCM + bcrypt)
│   │   ├── routes/
│   │   │   ├── auth.py           # /auth: login, register, me, profile, logout, change-password
│   │   │   ├── challenges.py     # /challenges: list, detail, submit flag
│   │   │   ├── admin.py          # /admin: stats, users, challenges CRUD, submissions
│   │   │   ├── lab.py            # /lab: start/stop/list lab instances
│   │   │   └── users.py          # /leaderboard, /users/{id}/profile
│   │   └── services/
│   │       ├── auth_service.py   # JWT create/decode, password hashing, user lookup
│   │       ├── challenge_service.py  # Challenge CRUD, flag submission, scoring
│   │       ├── admin_service.py  # User mgmt, stats, leaderboard, public profiles
│   │       └── lab_service.py    # Lab instance lifecycle (create, stop, cleanup, docker mgmt)
│   ├── main.py                   # Entry point (uvicorn.run)
│   ├── Dockerfile                # python:3.11-slim
│   └── requirements.txt
├── frontend/
│   └── dist/index.html           # SPA frontend (all JS/CSS inline)
├── nginx/nginx.conf              # Reverse proxy: /api/* -> backend, /* -> static files
├── lab/                          # Challenge lab directories (dynamic Docker targets)
├── scripts/                      # Deployment/utility scripts (currently empty)
├── docs/                         # Documentation (currently empty)
├── .relay/                       # Agent coordination logs (claude-codex progress tracking)
├── docker-compose.yml            # backend + redis + nginx
└── .env.example                  # Required env vars: SECRET_KEY, MASTER_KEY, FLAG_KEY
```

## Key Architectural Decisions

1. **Single-file frontend** — all HTML/CSS/JS in one file (`index.html`). No build step, no framework. State stored in `localStorage` for auth token.
2. **Service/Route separation** — routes handle HTTP concerns (parsing, validation, auth deps); services contain business logic and DB queries.
3. **Plaintext flag comparison** — flags are stored plaintext in DB (AES-GCM encryption via `crypto.py` is defined but `challenge_service.py` compares `flag_input.strip() == challenge.flag.strip()` directly).
4. **In-memory rate limiting** and **in-memory token blacklist** — resets on backend restart, suitable for CTF scale.
5. **Docker-in-Docker** — backend container mounts `/var/run/docker.sock` to spin up per-challenge lab containers dynamically.
6. **XSS prevention** — all user text fields sanitized via regex HTML tag stripping in auth/admin routes.

## Required Environment Variables

Must be set in `.env` or environment:
- `SECRET_KEY` — JWT signing key
- `MASTER_KEY` — Password encryption master key
- `FLAG_KEY` — Flag encryption key

## Common Commands

```bash
# Start full stack
docker-compose up -d

# Rebuild and start backend only
docker-compose up -d --build backend

# View logs
docker-compose logs -f backend

# Dev: run backend locally (SQLite)
pip install -r backend/requirements.txt
cd backend && python main.py
# App available at http://localhost:8000, docs at /docs

# Access running container shell
docker exec -it nu11cyber-backend /bin/bash
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/login | No | Login, returns JWT |
| POST | /auth/register | No | Register new user |
| GET | /auth/me | Yes | Current user info |
| PUT | /auth/profile | Yes | Update profile/avatar |
| POST | /auth/logout | Yes | Blacklist token |
| POST | /auth/change-password | Yes | Change password |
| GET | /challenges | No | List active challenges |
| GET | /challenges/:id | Yes | Challenge detail |
| POST | /challenges/submit | Yes | Submit flag |
| GET | /leaderboard | No | Top players |
| GET | /users/:id/profile | No | Public user profile |
| GET | /admin/stats | Admin | Platform stats |
| GET | /admin/users | Admin | List users |
| PUT | /admin/users/role | Admin | Change user role |
| DELETE | /admin/users/:id | Admin | Delete user |
| POST | /admin/challenges | Admin | Create challenge |
| PUT | /admin/challenges/:id | Admin | Update challenge |
| DELETE | /admin/challenges/:id | Admin | Delete challenge |
| GET | /admin/submissions | Admin | List flag submissions |
| GET | /admin/categories | Admin | List categories |
| POST | /lab/start | Yes | Deploy lab container |
| POST | /lab/:id/stop | Yes | Stop lab container |
| GET | /lab/list | Yes | User's lab instances |
| GET | /lab/:id | Yes | Lab status |
| GET | / | No | Health check |
| GET | /health | No | Health check |

## Notes

- Admin tab is auto-visible for users with `role = "admin"`
- Avatar images are stored as data URIs in the database (base64)
- Lab containers auto-expire after `LAB_CONTAINER_TIMEOUT` (default 3600s)
- Max concurrent labs per user: `MAX_CONCURRENT_LABS` (default 50)
- Rate limit: `RATE_LIMIT_PER_MINUTE` (default 20 req/min) on login/register
- Frontend API calls go through Nginx proxy at `/api/*` -> backend:8000
- Challenge difficulty: 1=Easy, 2=Medium, 3=Hard
