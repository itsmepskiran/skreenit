from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from models.notification_models import NotificationRequest
from datetime import datetime

router = APIRouter(tags=["notification"])

def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials missing")
    return create_client(supabase_url, supabase_key)

@router.post("/notify")
def send_notification(notification: NotificationRequest):
    client = get_supabase_client()

    notif = notification.dict()
    notif["created_at"] = datetime.utcnow().isoformat()

    result = client.table("notifications").insert(notif).execute()
    err = getattr(result, "error", None)
    if err:
        raise HTTPException(status_code=400, detail=f"Notification error: {err}")

    return {"ok": True, "data": result.data}
