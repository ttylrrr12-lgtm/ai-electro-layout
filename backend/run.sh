#!/usr/bin/env bash
set -e
# Activate venv and run uvicorn
if [ -d .venv ]; then source .venv/bin/activate; fi
export PYTHONUNBUFFERED=1
export PORT=${PORT:-8000}
uvicorn app:app --host 0.0.0.0 --port $PORT
