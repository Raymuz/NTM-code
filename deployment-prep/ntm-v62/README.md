# NTM v6.2 — Deployment Preparation (INCOMPLETE)

This is a source-only deployment checkpoint from Google Colab.

- `backend/` contains the previously tested **bounded FastAPI staging API**, not the full NTM system.
- `frontend/` contains only build preparation files, **not an executable app.py**.
- The original 40-tool/agent NTM Core has not yet been exported as a portable package.
- Real staff authentication, user/tenant-scoped state, and Docker deployment acceptance are pending.
- Publishing these files into `deployment-prep/ntm-v62/` **does not launch a Hugging Face app**.
- Do not promote this directory to the root of the Hugging Face Space.

Private notebooks, service account keys, API credentials, customer records and
runtime config files are intentionally excluded. Supply production secrets through
hosting secret settings later, not source control.
