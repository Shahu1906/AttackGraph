# ─────────────────────────────────────────────────────────────────────────────
# AttackGraphX Lab — Custom Flask App Container
#
# FOR AUTHORIZED LABORATORY USE ONLY.
# This image is intentionally minimal and should never be used in production.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

LABEL maintainer="AttackGraphX Lab"
LABEL description="Controlled HTTP target for AttackGraphX scanning lab"

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

# Run without debug in production-like mode inside the lab network
CMD ["python", "app.py"]
