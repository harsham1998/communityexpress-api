# WSGI wrapper for FastAPI to work with Render's Django detection
from app.main import app

# For compatibility with Render's gunicorn command
application = app