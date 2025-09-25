from fastapi import APIRouter, HTTPException, UploadFile, File, Header
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

@router.post("/general")
async def upload_general_video_unified(candidate_id: str = File(...), application_id: str = File(None), question_id: str = File(None), video: UploadFile = File(...), authorization: str | None = Header(default=None)):
    try:
        # This endpoint temporarily accepts both general video uploads as form-data
        # and job-specific response uploads; route by presence of application_id/question_id.
        contents = await video.read()
        # For demo, store fake URL; in production use storage and signed URLs
        video_url = f"https://your-storage/{candidate_id}/{application_id or 'general'}/{question_id or video.filename}"

        if application_id and question_id:
            # Save as a video response row
            payload = {
                "application_id": application_id,
                "question_id": question_id,
                "video_url": video_url,
                "status": "completed",
            }
            res = supabase.table("video_responses").upsert(payload).execute()
            if res.error:
                raise Exception(res.error)
            return {"status": "uploaded", "video_url": video_url}
        else:
            # Treat as general video; keep legacy for compatibility
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
