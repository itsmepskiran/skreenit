from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
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
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "added", "response": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add video response: {str(e)}")

@router.get("/application/{application_id}/responses")
def list_video_responses(application_id: str):
    try:
        res = supabase.table("video_responses").select("*").eq("application_id", application_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"responses": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch video responses: {str(e)}")

@router.post("/general")
async def upload_general_video_unified(
    candidate_id: str = Form(...),
    application_id: str = Form(None),
    question_id: str = Form(None),
    video: UploadFile = File(...),
    authorization: str = Header(default=None)
):
    try:
        contents = await video.read()
        # Use your object storage and signed URL logic here
        video_url = f"https://your-storage/{candidate_id}/{application_id or 'general'}/{question_id or video.filename}"

        if application_id and question_id:
            payload = {
                "application_id": application_id,
                "question_id": question_id,
                "video_url": video_url,
                "status": "completed",
            }
            res = supabase.table("video_responses").upsert(payload).execute()
        else:
            payload = {
                "candidate_id": candidate_id,
                "status": "completed",
                "video_url": video_url
            }
            res = supabase.table("general_video_interviews").upsert(payload).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "uploaded", "video_url": video_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload general video: {str(e)}")

@router.get("/general/{candidate_id}")
def get_general_video(candidate_id: str):
    try:
        res = supabase.table("general_video_interviews").select("*").eq("candidate_id", candidate_id).single().execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return res.data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"General video not found: {str(e)}")
