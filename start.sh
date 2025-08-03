#!/bin/bash
# Start script for FastAPI application
set -o errexit

# Use uvicorn directly - simpler and more reliable for FastAPI
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}