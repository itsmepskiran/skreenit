from typing import Optional
from supabase import Client
from .supabase_client import get_client

class DashboardService:
    def __init__(self, client: Optional[Client] = None) -> None:
        self.supabase = client or get_client()

    # TODO: Aggregation helpers for dashboards
