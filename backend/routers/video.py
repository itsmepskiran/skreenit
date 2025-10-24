from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Depends
from typing import Optional
import os
from models.video_models import VideoResponseRequest
from services.video_service import VideoService
from utils_others.security import get_user_from_bearer, ensure_role
from services.supabase_client import get_client

router = APIRouter(tags=["video"])

_supabase = None
_video_service = None

def get_supabase():
    global _supabase
    if _supabase is None:
        try:
            _supabase = get_client()
        except Exception as e:
            raise RuntimeError("Supabase client not configured: " + str(e)) from e
    return _supabase

def get_video_service():
    global _video_service
    if _video_service is None:
        supabase = get_supabase()
        _video_service = VideoService(supabase)
    return _video_service

def require_candidate(authorization: str = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.replace("Bearer ", "")
    try:
        user = get_user_from_bearer(token)
        ensure_role(user, "candidate")
        return user
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/response")
def add_video_response(payload: VideoResponseRequest, user: dict = Depends(require_candidate)):
    try:
        supabase = get_supabase()
        res = supabase.table("video_responses").insert(payload.dict()).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add video response: {str(e)}")

@router.get("/application/{application_id}/responses")
def list_video_responses(application_id: str, user: dict = Depends(require_candidate)):
    try:
        supabase = get_supabase()
        res = supabase.table("video_responses").select("*").eq("application_id", application_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch video responses: {str(e)}")

@router.post("/general")
async def upload_general_video_unified(
    candidate_id: str = Form(...),
    application_id: str = Form(None),
    question_id: str = Form(None),
    video: UploadFile = File(...),
    authorization: str = Header(default=None),
    user: dict = Depends(require_candidate)
):
    try:
        contents = await video.read()
        # Ensure we have a safe filename string for downstream storage APIs
        filename = video.filename or f"{candidate_id}_upload"
        filename = os.path.basename(filename)

        video_service = get_video_service()
        video_url = video_service.upload_video_to_storage(contents, filename, candidate_id)

        if application_id and question_id:
            db_result = video_service.save_video_response(
                application_id=application_id,
                question_id=question_id,
                video_url=video_url,
                duration=None,
                status="completed"
            )
        else:
            db_result = video_service.save_general_video(
                candidate_id=candidate_id,
                video_url=video_url,
                status="completed"
            )

        return {
            "ok": True,
            "data": {
                "status": "uploaded",
                "video_url": video_url,
                "database_record": db_result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload general video: {str(e)}")

@router.get("/general/{candidate_id}")
def get_general_video(candidate_id: str, user: dict = Depends(require_candidate)):
    try:
        supabase = get_supabase()
        res = supabase.table("general_video_interviews").select("*").eq("candidate_id", candidate_id).single().execute()
        if getattr(res, "error", None) or not getattr(res, "data", None):
            raise HTTPException(status_code=404, detail="General video not found")
        return {"ok": True, "data": res.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"General video not found: {str(e)}")

@router.get("/signed-url/{file_path:path}")
def get_signed_video_url(file_path: str, user: dict = Depends(require_candidate)):
    try:
        video_service = get_video_service()
        signed_url = video_service.create_signed_url(file_path, expires_in=3600)
        return {"ok": True, "data": {"signed_url": signed_url}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create signed URL: {str(e)}")
