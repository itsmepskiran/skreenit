from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum

class ApplicationStatus(str, Enum):
    submitted = "submitted"
    under_review = "under_review"
    video_pending = "video_pending"
    video_completed = "video_completed"
    interview_scheduled = "interview_scheduled"
    rejected = "rejected"
    hired = "hired"

class ApplicationRequest(BaseModel):
    job_id: str
    candidate_id: str
    status: Optional[ApplicationStatus] = ApplicationStatus.submitted
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    ai_score: Optional[int] = None
    ai_analysis: Optional[dict] = None
    recruiter_notes: Optional[str] = None

class CandidateProfileRequest(BaseModel):
    user_id: str
    title: Optional[str] = None
    bio: Optional[str] = None
    experience_years: Optional[int] = None
    current_salary: Optional[int] = None
    expected_salary: Optional[int] = None
    currency: Optional[str] = "INR"
    resume_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    availability: Optional[str] = None

class CandidateSkillRequest(BaseModel):
    candidate_id: str
    skill_name: str
    proficiency_level: Optional[str] = None
    years_experience: Optional[int] = None

class CandidateExperienceRequest(BaseModel):
    candidate_id: str
    company_name: str
    position: str
    description: Optional[str] = None
    start_date: Optional[str] = None  # ISO date
    end_date: Optional[str] = None    # ISO date
    is_current: Optional[bool] = False

class CandidateEducationRequest(BaseModel):
    candidate_id: str
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None  # ISO date
    end_date: Optional[str] = None    # ISO date
    grade: Optional[str] = None
