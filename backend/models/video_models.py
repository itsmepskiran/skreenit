from pydantic import BaseModel
from typing import Optional, Dict
from enum import Enum

class VideoStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class VideoResponseRequest(BaseModel):
    application_id: str
    question_id: str
    video_url: Optional[str] = None
    transcript: Optional[str] = None
    duration: Optional[int] = None
    ai_analysis: Optional[Dict] = None
    status: Optional[VideoStatus] = VideoStatus.not_started
    recorded_at: Optional[str] = None  # ISO datetime string

class GeneralVideoInterviewRequest(BaseModel):
    candidate_id: str
    status: VideoStatus = VideoStatus.not_started
    video_url: Optional[str] = None
    ai_analysis: Optional[Dict] = None
    created_at: Optional[str] = None  # ISO datetime string
