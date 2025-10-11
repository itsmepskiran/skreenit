import uuid
from datetime import datetime
from supabase import Client
from typing import Optional, Dict, Any

class VideoService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.bucket_name = "videos"

    def upload_video_to_storage(self, file_content: bytes, filename: str, candidate_id: str) -> str:
        try:
            file_extension = filename.split('.')[-1] if '.' in filename else 'mp4'
            unique_filename = f"{candidate_id}/{uuid.uuid4()}.{file_extension}"
            storage_response = self.supabase.storage.from_(self.bucket_name).upload(unique_filename, file_content)
            if getattr(storage_response, "error", None):
                raise Exception(f"Storage upload failed: {storage_response.error}")
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(unique_filename)
            return public_url
        except Exception as e:
            raise Exception(f"Video upload failed: {str(e)}")

    def create_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        try:
            signed_url = self.supabase.storage.from_(self.bucket_name).create_signed_url(file_path, expires_in)
            return signed_url['signedURL']
        except Exception as e:
            raise Exception(f"Failed to create signed URL: {str(e)}")

    def save_video_response(self, application_id: str, question_id: str, video_url: str,
                            transcript: Optional[str] = None, duration: Optional[int] = None, status: str = "completed") -> Dict[str, Any]:
        try:
            payload = {
                "application_id": application_id,
                "question_id": question_id,
                "video_url": video_url,
                "transcript": transcript,
                "duration": duration,
                "status": status,
                "recorded_at": datetime.utcnow().isoformat()
            }
            res = self.supabase.table("video_responses").insert(payload).execute()
            if getattr(res, "error", None):
                raise Exception(res.error)
            return res.data[0] if res.data else None
        except Exception as e:
            raise Exception(f"Failed to save video response: {str(e)}")

    def save_general_video(self, candidate_id: str, video_url: str, status: str = "completed", ai_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            payload = {
                "candidate_id": candidate_id,
                "video_url": video_url,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
                "is_general": True,
                "ai_analysis": ai_analysis or {}
            }
            res = self.supabase.table("general_video_interviews").upsert(payload, on_conflict="candidate_id").execute()
            if getattr(res, "error", None):
                raise Exception(res.error)
            return res.data[0] if res.data else None
        except Exception as e:
            raise Exception(f"Failed to save general video: {str(e)}")

    def get_video_responses(self, application_id: str) -> Dict[str, Any]:
        try:
            res = self.supabase.table("video_responses").select("*").eq("application_id", application_id).execute()
            if getattr(res, "error", None):
                raise Exception(res.error)
            return {"responses": res.data}
        except Exception as e:
            raise Exception(f"Failed to fetch video responses: {str(e)}")

    def get_candidate_videos(self, candidate_id: str) -> Dict[str, Any]:
        try:
            res = self.supabase.table("video_responses").select("*").eq("candidate_id", candidate_id).execute()
            if getattr(res, "error", None):
                raise Exception(res.error)
            return {"videos": res.data}
        except Exception as e:
            raise Exception(f"Failed to fetch candidate videos: {str(e)}")
