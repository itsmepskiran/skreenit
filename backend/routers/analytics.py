from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from models.analytics_models import AnalyticsEventRequest

router = APIRouter(tags=["analytics"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.post("/")
def create_event(payload: AnalyticsEventRequest):
    try:
        res = supabase.table("analytics_events").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "created", "event": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create event")

@router.get("/user/{user_id}")
def list_events(user_id: str):
    try:
        res = supabase.table("analytics_events").select("*").eq("user_id", user_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"events": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch events")