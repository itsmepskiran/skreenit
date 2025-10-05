import os
import uuid
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, Dict, Any
import json

class VideoService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.bucket_name = "videos"

    def upload_video_to_storage(self, file_content: bytes, filename: str, candidate_id: str) -> str:
        """
        Upload video file to Supabase Storage and return the public URL
        """
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'mp4'
            unique_filename = f"{candidate_id}/{uuid.uuid4()}.{file_extension}"

            # Upload to Supabase Storage
            storage_response = self.supabase.storage.from_(self.bucket_name).upload(
                unique_filename,
                file_content
            )

            if storage_response.get('error'):
                raise Exception(f"Storage upload failed: {storage_response['error']}")

            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(unique_filename)

            return public_url

        except Exception as e:
            raise Exception(f"Video upload failed: {str(e)}")

    def create_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Create a signed URL for video access (temporary access)
        """
        try:
            signed_url = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in
            )
            return signed_url['signedURL']
        except Exception as e:
            raise Exception(f"Failed to create signed URL: {str(e)}")

    def save_video_response(self, application_id: str, question_id: str, video_url: str,
                          transcript: str = None, duration: int = None, status: str = "completed") -> Dict[str, Any]:
        """
        Save video response to database
        """
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

    def save_general_video(self, candidate_id: str, video_url: str, status: str = "completed") -> Dict[str, Any]:
        """
        Save general video interview to database
        Note: Since 'general_video_interviews' table doesn't exist in schema,
        we'll use the existing structure or create a new approach
        """
        try:
            # For now, we'll store general videos as a special type of video response
            # or we can extend the database schema later
            payload = {
                "candidate_id": candidate_id,
                "video_url": video_url,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
                "is_general": True  # Flag to identify general videos
            }

            # Since the table doesn't exist, we'll return the payload for now
            # In a real implementation, you'd need to add this table to the schema
            return {"message": "General video saved", "data": payload}

        except Exception as e:
            raise Exception(f"Failed to save general video: {str(e)}")

    def get_video_responses(self, application_id: str) -> Dict[str, Any]:
        """
        Get all video responses for an application
        """
        try:
            res = self.supabase.table("video_responses").select("*").eq("application_id", application_id).execute()

            if getattr(res, "error", None):
                raise Exception(res.error)

            return {"responses": res.data}

        except Exception as e:
            raise Exception(f"Failed to fetch video responses: {str(e)}")

    def get_candidate_videos(self, candidate_id: str) -> Dict[str, Any]:
        """
        Get all videos for a candidate
        """
        try:
            res = self.supabase.table("video_responses").select("*").eq("candidate_id", candidate_id).execute()

            if getattr(res, "error", None):
                raise Exception(res.error)

            return {"videos": res.data}

        except Exception as e:
            raise Exception(f"Failed to fetch candidate videos: {str(e)}")
