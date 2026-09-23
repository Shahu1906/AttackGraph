# ─────────────────────────────────────────────────────────────────────────────
# AttackGraphX Recon Service — Dockerfile
#
# Builds a self-contained image with:
#   - Python 3.11
#   - Nmap (installed via apt)
#   - All Python dependencies
#   - Application code
#
# Run with: docker compose up recon-service
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

LABEL maintainer="AttackGraphX Team"
LABEL description="AttackGraphX Person 1 — Recon Service"

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nmap \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY app/ ./app/

# ── Non-root user for security ────────────────────────────────────────────────
# Note: Nmap requires elevated privileges for raw socket scans (-sS).
# For lab use, running as root is acceptable.
# For production hardening, consider: --cap-add=NET_RAW --cap-add=NET_ADMIN
# RUN useradd -m appuser && chown -R appuser:appuser /app
# USER appuser

EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start Uvicorn ─────────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
