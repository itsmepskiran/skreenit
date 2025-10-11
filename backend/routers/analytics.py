from fastapi import APIRouter, HTTPException, Header
import os
from supabase import create_client, Client
from models.analytics_models import AnalyticsEventRequest
from datetime import datetime
from utils_others.security import get_user_from_bearer

router = APIRouter(tags=["analytics"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.post("/")
async def create_event(payload: AnalyticsEventRequest, authorization: str = Header(default=None)):
    try:
        data = payload.dict()
        data["created_at"] = datetime.utcnow().isoformat()
        # If bearer is present, prefer user_id from token to avoid spoofing
        if authorization and authorization.startswith("Bearer "):
            try:
                token = authorization.replace("Bearer ", "")
                user = get_user_from_bearer(token)
                data["user_id"] = user.get("id")
            except Exception:
                pass
        res = supabase.table("analytics_events").insert(data).execute()
        if getattr(res, "error", None):
            raise Exception(f"Analytics insert error: {res.error}")
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@router.get("/user/{user_id}")
def list_events(user_id: str):
    try:
        res = supabase.table("analytics_events").select("*").eq("user_id", user_id).execute()
        if getattr(res, "error", None):
            raise Exception(f"Analytics fetch error: {res.error}")
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")
