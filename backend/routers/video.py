from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from models.video_models import VideoResponseRequest

router = APIRouter(tags=["video"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.post("/response")
def add_video_response(payload: VideoResponseRequest):
    try:
        res = supabase.table("video_responses").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "response": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add video response")

@router.get("/application/{application_id}/responses")
def list_video_responses(application_id: str):
    try:
        res = supabase.table("video_responses").select("*").eq("application_id", application_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"responses": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch video responses")