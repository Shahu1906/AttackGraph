# AttackGraphX API Gateway

> **Person 3 — API Gateway & Dashboard Service**
> FastAPI • JWT Auth • RBAC • Redis Cache • PDF/CSV Reports

---

## Overview

This is the API gateway that sits between the React frontend and the upstream analysis service (Persons 1 & 2). It provides:

| Responsibility | Implementation |
|---|---|
| JWT Authentication | `python-jose` + `passlib[bcrypt]` |
| Role-Based Access Control | FastAPI `Depends` — admin / analyst |
| Analysis Service Client | `httpx` async with 3-attempt retry |
| Redis Last-Known-Good Cache | `redis.asyncio` — stale_cache fallback |
| Health Endpoint | `/health` — probes all dependencies |
| PDF Reports | `ReportLab` — professional security assessment |
| CSV Export | Structured telemetry — all path fields |
| Tests | `pytest` — auth, RBAC, paths, cache, reports, health |

---

## Quick Start

### 1. Install Dependencies

```powershell
cd d:\TY\EDI\attack\backend
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
copy .env.example .env
# Edit .env — set JWT_SECRET, ANALYSIS_SERVICE_URL, REDIS_URL
```

### 3. Start Redis

```powershell
# Docker (recommended)
docker run -d -p 6379:6379 redis:alpine

# Or Redis for Windows native
redis-server
```

### 4. Start the Gateway

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Docs available at: http://localhost:8000/docs

---

## Connect the Frontend

In `d:\TY\EDI\attack\frontend\.env` (or `.env.local`):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=false
```

Then start the frontend:

```powershell
cd d:\TY\EDI\attack\frontend
npm run dev
```

> **Note:** `VITE_USE_MOCK=false` connects to the real backend. `VITE_USE_MOCK=true` runs with mock data for offline development.

---

## API Endpoints

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| `POST` | `/auth/login` | ❌ | — | Get JWT token |
| `GET` | `/health` | ❌ | — | Service health |
| `GET` | `/paths` | ✅ | any | Attack paths |
| `GET` | `/patches` | ✅ | any | Remediation patches |
| `GET` | `/scan/status` | ✅ | any | Scan status |
| `POST` | `/simulate` | ✅ | **admin** | What-If simulation |
| `POST` | `/simulate/reset` | ✅ | **admin** | Reset simulations |
| `GET` | `/scan/trigger` | ✅ | **admin** | Trigger scan |
| `GET` | `/reports/pdf` | ✅ | any | Download PDF report |
| `GET` | `/reports/csv` | ✅ | any | Download CSV export |

---

## Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `analyst` | `analyst123` | analyst |

> Passwords are stored as bcrypt hashes — never in plaintext.

---

## Resilience Model

```
Frontend → FastAPI
             ↓
         Analysis Service (try 1→2→3 with backoff)
             ↓ success           ↓ failure
         Cache in Redis      Try Redis
             ↓                   ↓ hit          ↓ miss
         status: live        stale_cache     unavailable
```

The frontend `status` field distinguishes all three states and renders the appropriate UI banner.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Port |
| `JWT_SECRET` | *(required)* | HS256 signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRATION_MINUTES` | `60` | Token lifetime |
| `ANALYSIS_SERVICE_URL` | `http://localhost:9000` | Upstream analysis service |
| `ANALYSIS_TIMEOUT` | `10` | Request timeout (seconds) |
| `ANALYSIS_RETRIES` | `3` | Max retry attempts |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `REDIS_TTL` | `300` | Cache TTL (seconds) |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allow origin |

---

## Run Tests

```powershell
cd d:\TY\EDI\attack\backend
pytest tests/ -v --tb=short
```

Tests cover: auth, RBAC, paths live/stale/unavailable, cache write/read, reports PDF/CSV, health dependencies.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, routers
│   ├── config.py            # Pydantic settings from .env
│   ├── auth/
│   │   ├── jwt.py           # create/verify token
│   │   ├── dependencies.py  # get_current_user, require_admin
│   │   └── routes.py        # POST /auth/login
│   ├── routes/
│   │   ├── paths.py         # GET /paths, /patches
│   │   ├── whatif.py        # POST /simulate, /simulate/reset, /scan/*
│   │   ├── reports.py       # GET /reports/pdf, /reports/csv
│   │   └── health.py        # GET /health
│   ├── services/
│   │   ├── analysis_client.py  # httpx async client, retry logic
│   │   ├── cache_service.py    # Redis last-known-good cache
│   │   └── report_service.py   # ReportLab PDF + CSV generation
│   ├── schemas/
│   │   ├── auth.py          # LoginRequest, TokenResponse
│   │   ├── paths.py         # PathModel, PatchModel, responses
│   │   ├── dashboard.py     # SimulateRequest/Response
│   │   └── reports.py       # ReportRequest
│   └── utils/
│       └── errors.py        # Consistent error envelope
├── tests/
│   ├── conftest.py          # Fixtures, sample data, TestClient helpers
│   ├── test_auth.py
│   ├── test_paths.py
│   ├── test_whatif.py
│   ├── test_reports.py
│   ├── test_health.py
│   └── test_cache.py
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```
