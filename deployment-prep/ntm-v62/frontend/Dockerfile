# ==========================================================
# NTM V6.2 — THREE-PANEL GRADIO FRONTEND
# Source prepared; production deployment not yet verified
# ==========================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONNOUSERSITE=1

ENV PORT=7860
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860
ENV GRADIO_TEMP_DIR=/tmp/ntm_ui

WORKDIR /app

# Install existing approved frontend requirements.
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir \
    --disable-pip-version-check \
    -r /app/requirements.txt

# Create a non-root runtime account.
RUN groupadd --gid 10002 ntmui \
    && useradd --uid 10002 --gid 10002 \
       --create-home --shell /usr/sbin/nologin ntmui \
    && mkdir -p /tmp/ntm_ui \
    && chown -R 10002:10002 /tmp/ntm_ui /app

# Three-panel Gradio application and API integration.
COPY --chown=10002:10002 app.py /app/
COPY --chown=10002:10002 ntm_api_client.py /app/
COPY --chown=10002:10002 ntm_service_bridge.py /app/

# Frontend service contract.
COPY --chown=10002:10002 ui_contract.json /app/

# Approved NTM branding and document template.
COPY --chown=10002:10002 NTM_logo_web.png /app/
COPY --chown=10002:10002 YDOO-NTM-logo.png /app/
COPY --chown=10002:10002 NTM_Letterhead_Fillable_Correspondence.docx /app/

# NTM_API_BASE_URL must be configured at deployment runtime.
# Set NTM_API_SERVICE_TOKEN securely if the backend requires it.
# Do not bake credentials into this image.

ENV HOME=/home/ntmui
USER 10002:10002

EXPOSE 7860

# Existing Gradio entrypoint.
# Do not use uvicorn unless app.py exports an ASGI app.
CMD ["python", "app.py"]
