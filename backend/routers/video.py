from fastapi import APIRouter, HTTPException, UploadFile, File
from supabase import create_client, Client
import os
from models.video_models import VideoResponseRequest, GeneralVideoInterviewRequest

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

# --- General Video Interview Endpoints ---

@router.post("/general/{candidate_id}")
async def upload_general_video(candidate_id: str, video: UploadFile = File(...)):
    try:
        # You should implement actual file upload to storage here and get the public URL
        # For demo, we'll just use the filename
        video_url = f"https://your-storage/{candidate_id}/{video.filename}"
        payload = {
            "candidate_id": candidate_id,
            "status": "completed",
            "video_url": video_url
        }
        res = supabase.table("general_video_interviews").upsert(payload).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "uploaded", "video_url": video_url}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload general video")

@router.get("/general/{candidate_id}")
def get_general_video(candidate_id: str):
    try:
        res = supabase.table("general_video_interviews").select("*").eq("candidate_id", candidate_id).single().execute()
        if res.error:
            raise Exception(res.error)
        return res.data
    except Exception:
        raise HTTPException(status_code=404, detail="General video not found")
