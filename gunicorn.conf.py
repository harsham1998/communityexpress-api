# This file tells Render this is NOT a Django project
# FastAPI should use uvicorn, not gunicorn
import os

# Use uvicorn worker for ASGI applications like FastAPI
worker_class = "uvicorn.workers.UvicornWorker"
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = 1
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2