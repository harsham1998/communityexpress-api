import os
from dotenv import load_dotenv
from pathlib import Path

# Get the directory where this config.py file is located
current_dir = Path(__file__).parent
# Go to the backend directory (parent of app)
backend_dir = current_dir.parent
# Look for .env file in the backend directory
env_path = backend_dir / ".env"

# Load environment variables
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))