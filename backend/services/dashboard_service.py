from typing import Optional
from supabase import Client
from .supabase_client import get_client

class DashboardService:
    def __init__(self, client: Optional[Client] = None):
        self.supabase = client or get_client()

    def get_summary(self, user_id: str) -> dict:
        """
        Logic for fetching dashboard summary data — customize per business rules.
        """
        user_resp = self.supabase.table("users").select("role").eq("id", user_id).single().execute()
        if getattr(user_resp, "error", None):
            raise Exception(f"User fetch error: {user_resp.error}")
        role = user_resp.data.get("role")
        # Further logic can be added here
        return {"user_id": user_id, "role": role}
