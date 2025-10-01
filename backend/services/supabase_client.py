import os
from supabase import create_client, Client

def get_client() -> Client:
    """
    Returns a Supabase client using environment variables for credentials.
    Ensures proper error handling if variables are missing.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials are not set in the environment variables.")
    return create_client(supabase_url, supabase_key)
