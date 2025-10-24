from fastapi import APIRouter, HTTPException, Header
from models.analytics_models import AnalyticsEventRequest
from datetime import datetime
from utils_others.security import get_user_from_bearer
from services.supabase_client import get_client

router = APIRouter(tags=["analytics"])

_supabase = None

def get_supabase_client():
    global _supabase
    if _supabase is None:
        try:
            _supabase = get_client()
        except Exception as e:
            raise RuntimeError("Supabase client not configured: " + str(e)) from e
    return _supabase

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
        supabase = get_supabase_client()
        res = supabase.table("analytics_events").insert(data).execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Analytics insert error: {err}")
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@router.get("/user/{user_id}")
def list_events(user_id: str):
    try:
        supabase = get_supabase_client()
        res = supabase.table("analytics_events").select("*").eq("user_id", user_id).execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Analytics fetch error: {err}")
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")
