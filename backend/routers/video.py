from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from supabase import create_client, Client
import os
from ..models.video_models import VideoResponseRequest
from ..services.video_service import VideoService

router = APIRouter(tags=["video"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize video service
video_service = VideoService(supabase)

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
        # Read video file
        contents = await video.read()

        # Upload to Supabase Storage using the service
        video_url = video_service.upload_video_to_storage(
            file_content=contents,
            filename=video.filename,
            candidate_id=candidate_id
        )

        # Save to database based on context
        if application_id and question_id:
            # This is a response to a specific interview question
            db_result = video_service.save_video_response(
                application_id=application_id,
                question_id=question_id,
                video_url=video_url,
                duration=None,  # Could be extracted from video metadata
                status="completed"
            )
        else:
            # This is a general video interview
            db_result = video_service.save_general_video(
                candidate_id=candidate_id,
                video_url=video_url,
                status="completed"
            )

        return {
            "status": "uploaded",
            "video_url": video_url,
            "database_record": db_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload general video: {str(e)}")

@router.get("/general/{candidate_id}")
def get_general_video(candidate_id: str):
    try:
        # Get candidate's video responses (general videos are stored as video responses)
        videos = video_service.get_candidate_videos(candidate_id)

        # Filter for general videos if needed
        general_videos = [v for v in videos.get("videos", []) if v.get("is_general", False)]

        if not general_videos:
            raise HTTPException(status_code=404, detail="General video not found")

        return general_videos[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"General video not found: {str(e)}")

@router.get("/signed-url/{file_path:path}")
def get_signed_video_url(file_path: str):
    """
    Get a signed URL for temporary access to a video file
    """
    try:
        signed_url = video_service.create_signed_url(file_path, expires_in=3600)  # 1 hour expiry
        return {"signed_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create signed URL: {str(e)}")
