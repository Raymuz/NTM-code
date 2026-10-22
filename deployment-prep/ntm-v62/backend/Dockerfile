# ==========================================================
# NTM V6.2 — FASTAPI BACKEND
# Bounded staging runtime; production certification pending
# ==========================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONNOUSERSITE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV NTM_ENV=staging
ENV HOME=/home/ntm

WORKDIR /app

# Install only the previously verified backend dependencies.
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir -r /app/requirements.txt && groupadd --gid 10001 ntm && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin ntm && mkdir -p /tmp/ntm_backend && chown -R 10001:10001 /app /tmp/ntm_backend

# Copy bounded FastAPI application source.
COPY --chown=10001:10001 api.py ntm_catalog.py ntm_verified_runtime.py ntm_verified_content.py ntm_floor_plan_agent.py ntm_master_1a_policy.py ui_contract.json /app/

# Do not copy ntm_core until all original tool
# implementations and dependencies are verified.

# Configure runtime credentials through deployment secrets.
# Never include real keys in this Dockerfile.

USER 10001:10001

EXPOSE 8000

# Healthcheck verifies the FastAPI process is responding.
# It does not establish full NTM Core readiness.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3).close()"

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
