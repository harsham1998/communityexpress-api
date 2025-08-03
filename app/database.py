from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(f"Missing Supabase configuration: URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_KEY)}")
    return create_client(SUPABASE_URL, SUPABASE_KEY)