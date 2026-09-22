# AttackGraphX — Person 1: Recon Service

> **⚠️ AUTHORIZED LAB USE ONLY**
> This project is a controlled cybersecurity laboratory.
> All scanning is restricted to the internal Docker network.
> Do NOT use this to scan external or public networks.

---

## 1. Project Purpose

**AttackGraphX** is an AI-driven attack path discovery and security risk prioritization system.

This repository implements **Person 1's component**: the **Recon Service**.

The Recon Service:
- Creates a controlled, isolated Docker-based simulated enterprise network
- Runs Nmap scans against that network
- Converts Nmap XML into a standardized JSON schema
- Validates results with Pydantic
- Publishes results to Redis Streams for Person 2 (Analysis Service) to consume

**Your responsibility ends at Redis. You never call Person 2's API directly.**

---

## 2. Person 1's Responsibilities

| Area | Description |
|---|---|
| Simulated Range | Docker-based fake enterprise network (web, FTP, Flask) |
| Nmap Runner | Execute Nmap safely via subprocess |
| XML Parser | Parse Nmap XML using defusedxml |
| Normalizer | Convert Nmap data → AttackGraphX schema |
| Pydantic Validation | Validate before publishing |
| Redis Publisher | Publish JSON to `scan_results` stream |
| FastAPI | `POST /scan`, `GET /scan/{id}`, `GET /health` |
| Scheduler | Periodic auto-scanning |
| Tests | Unit + integration test suite |

**Not implemented here**: Neo4j, Dijkstra, Yen's algorithm, React dashboard, JWT/RBAC, PDF reports.

---

## 3. Architecture

```
User / Scheduler
       ↓
POST /scan
       ↓
Recon Service (FastAPI)
       ↓
Nmap (subprocess, no shell=True)
       ↓
Nmap XML (-oX -)
       ↓
XML Parser (defusedxml)
       ↓
Normalizer
       ↓
Pydantic Validation (ScanResult)
       ↓
Redis Stream: scan_results
       ↓
Person 2 Analysis Service
```

### Network Topology

```
attackgraphx-net (172.20.0.0/24)
├── recon-service    (scans targets)
├── web-server       172.20.0.10  :80
├── ftp-server       172.20.0.11  :21
└── custom-flask-app 172.20.0.12  :5000

recon-internal (isolated)
├── recon-service
└── redis
```

---

## 4. Docker Range

Three intentionally weak lab services:

| Container | Image | IP | Port | Purpose |
|---|---|---|---|---|
| `web-server` | nginx:1.25-alpine | 172.20.0.10 | 80/tcp | HTTP target |
| `ftp-server` | fauria/vsftpd | 172.20.0.11 | 21/tcp | FTP target |
| `custom-flask-app` | Custom Dockerfile | 172.20.0.12 | 5000/tcp | HTTP/Flask target |

All containers are on the `attackgraphx-net` bridge network.
None are exposed to the public internet.

---

## 5. Nmap Scanning

The scanner:
- **Validates** the target is within `RANGE_CIDR` using Python's `ipaddress` stdlib
- **Rejects** any target outside the authorized range
- Runs: `nmap -sV -T4 -oX - <target>` (configurable via `NMAP_SCAN_FLAGS`)
- Returns raw XML — no shell=True, no string interpolation

---

## 6. JSON Contract

The canonical schema published to Redis:

```json
{
  "scan_id": "scan-a3f2b891",
  "timestamp": "2026-09-22T10:30:00+00:00",
  "scanner": "nmap",
  "target_scope": "172.20.0.0/24",
  "hosts": [
    {
      "ip": "172.20.0.10",
      "hostname": "web-server",
      "state": "up",
      "segment": "web",
      "services": [
        {
          "port": 80,
          "protocol": "tcp",
          "state": "open",
          "name": "http",
          "product": "nginx",
          "version": "1.25.0",
          "extra_info": null
        }
      ],
      "vulnerabilities": [],
      "credentials": []
    }
  ]
}
```

**Person 2 should consume this schema from Redis Streams.**

---

## 7. Redis Integration

- **Stream key**: `scan_results`
- **Method**: `XADD` (Redis Streams) — durable, replayable
- **Fields per entry**: `scan_id`, `target`, `data` (full JSON)
- **Person 2 consumer**: Use `XREAD` or a consumer group on `scan_results`

---

## 8. API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check (nmap + redis status) |
| `POST` | `/scan` | Trigger an on-demand scan |
| `GET` | `/scan/{scan_id}` | Get scan status |
| `GET` | `/scans` | List all scans |

### POST /scan

**Request:**
```json
{ "target": "172.20.0.0/24" }
```

**Response (202 Accepted):**
```json
{
  "scan_id": "scan-a3f2b891",
  "status": "queued",
  "message": "Scan queued for target '172.20.0.0/24'. Check status at GET /scan/scan-a3f2b891"
}
```

### GET /health

```json
{
  "status": "healthy",
  "scanner": "available",
  "redis": "connected",
  "last_successful_scan": "2026-09-22T10:30:00+00:00",
  "version": "1.0.0"
}
```

---

## 9. Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `REDIS_TOPIC` | `scan_results` | Redis Stream key |
| `REDIS_MAX_RETRIES` | `3` | Publish retry attempts |
| `RANGE_CIDR` | `172.20.0.0/24` | **Authorized scan range only** |
| `RANGE_NETWORK` | `attackgraphx-net` | Docker network name |
| `NMAP_SCAN_FLAGS` | `-sV -T4` | Nmap flags |
| `NMAP_TIMEOUT_SECONDS` | `300` | Max scan duration |
| `SCAN_INTERVAL_MINUTES` | `30` | Auto-scan interval (0=disabled) |
| `SCAN_DEFAULT_TARGET` | `172.20.0.0/24` | Scheduled scan target |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 10. How to Start the System

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose V2

### Steps

```bash
# 1. Clone / navigate to the recon-service directory
cd recon-service

# 2. Copy the environment template
copy .env.example .env

# 3. Start the full stack
docker compose up --build -d

# 4. Verify all containers are running
docker compose ps
```

Expected output:
```
NAME                    STATUS
attackgraphx-recon      running (healthy)
attackgraphx-redis      running (healthy)
attackgraphx-web        running (healthy)
attackgraphx-ftp        running
attackgraphx-flask      running (healthy)
```

---

## 11. How to Perform a Scan

### On-demand scan via API

```bash
# Trigger a scan of the full lab range
curl -X POST http://localhost:8000/scan \
     -H "Content-Type: application/json" \
     -d '{"target": "172.20.0.0/24"}'
```

Response:
```json
{"scan_id": "scan-a3f2b891", "status": "queued", ...}
```

```bash
# Check scan status
curl http://localhost:8000/scan/scan-a3f2b891

# List all scans
curl http://localhost:8000/scans

# Check service health
curl http://localhost:8000/health
```

### Swagger UI

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API docs.

---

## 12. How to Inspect Redis

```bash
# Open Redis CLI inside the container
docker exec -it attackgraphx-redis redis-cli

# Read all entries from the scan_results stream
XREAD COUNT 10 STREAMS scan_results 0

# Read the latest 5 entries
XREVRANGE scan_results + - COUNT 5

# Check stream length
XLEN scan_results

# Get stream info
XINFO STREAM scan_results
```

---

## 13. How to Run Unit Tests

Unit tests do NOT require Docker or Nmap:

```bash
# Install dependencies (in a virtual environment)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Linux/Mac

pip install -r requirements.txt

# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ -v --tb=short
```

---

## 14. How to Run Integration Tests

Integration tests require Docker + Nmap installed on your machine:

```bash
# Install Docker Python SDK (already in requirements.txt)
pip install docker

# Run integration tests
python -m pytest tests/integration/ -v -s

# Run everything
python -m pytest tests/ -v
```

Tests are automatically **skipped** (not failed) if Docker or Nmap is unavailable.

---

## 15. Troubleshooting

### "nmap not found"
- The `recon-service` Docker container includes nmap — check container is running
- For local dev: install nmap from https://nmap.org/download.html
- Windows: add nmap to your PATH after installation

### "Redis connection failed"
- Check Redis container: `docker compose logs redis`
- Verify REDIS_URL in your `.env` points to `redis://redis:6379/0` when using Docker
- For local dev: use `redis://localhost:6379/0`

### "Target outside authorized range"
- Only `172.20.0.0/24` (or subnets of it) are permitted by default
- Change `RANGE_CIDR` in `.env` if you reconfigure the lab network

### FTP container fails to start
- The `fauria/vsftpd` image may take 10–15 seconds to initialize
- Check: `docker compose logs ftp-server`

### Scan stays in "queued" status
- The background task may have crashed — check logs: `docker compose logs recon-service`
- Nmap inside the container needs `NET_RAW` capability (included in compose file)

---

## 16. Security & Scope Restrictions

> **This system is designed for an isolated, authorized laboratory environment.**

| Restriction | How it's enforced |
|---|---|
| Only scan authorized targets | `validate_target()` in `nmap_runner.py` — rejects anything outside `RANGE_CIDR` |
| No shell injection | `subprocess.run(shell=False)` with argument list |
| No XXE attacks | `defusedxml` used for all XML parsing |
| No external credentials | All test credentials are fake, lab-only values |
| Isolated network | Lab containers only accessible on `attackgraphx-net` bridge network |
| No direct Person 2 calls | Redis is the only coupling point between Person 1 and Person 2 |

**Do not:**
- Point `RANGE_CIDR` at a public IP range
- Expose lab containers to the internet
- Use any credentials from this lab in real systems
