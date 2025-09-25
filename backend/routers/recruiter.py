from fastapi import APIRouter, HTTPException, Header, Depends
from supabase import create_client, Client
import os
from models.recruiter_models import JobPostRequest
from models.recruiter_models import JobSkillRequest
from models.recruiter_models import RecruiterProfileRequest
from services.recruiter_service import RecruiterService
from utils_others.security import get_user_from_bearer, ensure_role, AuthUser

router = APIRouter(tags=["recruiter"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
service = RecruiterService(supabase)

# ---- Auth dependency ----
def require_recruiter(authorization: str | None = Header(default=None)) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.replace("Bearer ", "")
    try:
        user = get_user_from_bearer(token)
        ensure_role(user, "recruiter")
        return user
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/post-job")
def post_job(payload: JobPostRequest, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.post_job(payload.dict())
    except Exception:
        raise HTTPException(status_code=500, detail="Job post failed")

@router.get("/jobs")
def list_jobs(user: AuthUser = Depends(require_recruiter)):
    try:
        return service.list_jobs()
    except Exception:
        raise HTTPException(status_code=500, detail="Could not fetch jobs")

@router.get("/job/{job_id}")
def get_job(job_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.get_job(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

@router.put("/job/{job_id}")
def update_job(job_id: str, payload: JobPostRequest, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.update_job(job_id, payload.dict(exclude_unset=True))
    except Exception:
        raise HTTPException(status_code=500, detail="Job update failed")

@router.delete("/job/{job_id}")
def delete_job(job_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.delete_job(job_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Job delete failed")

@router.post("/profile")
def create_recruiter_profile(payload: RecruiterProfileRequest, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.upsert_profile(payload.dict())
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save recruiter profile")

@router.get("/profile/{user_id}")
def get_recruiter_profile(user_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.get_profile(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

@router.post("/application/{application_id}/approve")
def approve_application(application_id: str, user: AuthUser = Depends(require_recruiter)):
    """Mark an application as under_review and notify the candidate via Resend (best-effort)."""
    try:
        return service.approve_application(application_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to approve application")


@router.post("/job/{job_id}/questions")
def create_job_questions(job_id: str, payload: list[dict], user: AuthUser = Depends(require_recruiter)):
    """Create or replace job questions for a job. Expects list of {question_text, question_order, time_limit}."""
    try:
        return service.save_job_questions(job_id, payload)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save questions")


@router.get("/job/{job_id}/questions")
def list_job_questions(job_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.list_job_questions(job_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.get("/application/{application_id}/resume-url")
def get_application_resume_url(application_id: str, user: AuthUser = Depends(require_recruiter)):
    """Return a signed resume URL for the application's candidate if the recruiter owns the job.
    Authorization: validated by checking jobs.created_by for the given application.
    """
    try:
        return service.get_application_resume_url(application_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch resume URL")

@router.get("/companies")
def list_companies(user: AuthUser = Depends(require_recruiter)):
    try:
        return service.list_companies()
    except Exception:
        raise HTTPException(status_code=500, detail="Could not fetch companies")

@router.get("/job/{job_id}/applications")
def list_job_applications(job_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.list_job_applications(job_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Could not fetch applications")

@router.get("/applicants")
def list_applicants(company_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        return service.list_applicants(company_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Applicant fetch failed")

@router.post("/job/{job_id}/skills")
def add_job_skill(job_id: str, payload: JobSkillRequest, user: AuthUser = Depends(require_recruiter)):
    try:
        # Keep inline (or could add to service if needed)
        res = supabase.table("job_skills").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "skill": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add skill")

@router.get("/job/{job_id}/skills")
def list_job_skills(job_id: str, user: AuthUser = Depends(require_recruiter)):
    try:
        # Keep inline (or could add to service if needed)
        res = supabase.table("job_skills").select("*").eq("job_id", job_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"skills": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch skills")
