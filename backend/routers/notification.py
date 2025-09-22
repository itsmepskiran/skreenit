from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from models.notification_models import NotificationRequest

router = APIRouter(tags=["notification"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.post("/")
def create_notification(payload: NotificationRequest):
    try:
        res = supabase.table("notifications").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "created", "notification": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create notification")

@router.get("/user/{user_id}")
def list_notifications(user_id: str):
    try:
        res = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"notifications": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")