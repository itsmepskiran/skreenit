from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request, Header, Depends
from fastapi import Body
from supabase import create_client, Client
import os, secrets, httpx
from typing import Any, Dict, List, Optional
from models.applicant_models import ApplicationRequest
from models.applicant_models import CandidateEducationRequest
from models.applicant_models import CandidateExperienceRequest
from models.applicant_models import CandidateSkillRequest
from services.applicant_service import ApplicantService
from utils_others.security import get_user_from_bearer, ensure_role, AuthUser

router = APIRouter(tags=["applicant"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize service (can be swapped for dependency injection in future)
applicant_service = ApplicantService(supabase)

# ---- Auth dependencies ----
def require_candidate(authorization: str | None = Header(default=None)) -> AuthUser:
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

@router.post("/apply")
def apply_job(payload: ApplicationRequest, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("job_applications").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "applied", "data": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Application failed")

@router.post("/upload-resume")
async def upload_resume(applicant_id: str = Form(...), resume: UploadFile = File(...), user: AuthUser = Depends(require_candidate)):
    try:
        content = await resume.read()
        return applicant_service.upload_resume(
            candidate_id=applicant_id,
            filename=resume.filename,
            content=content,
            content_type=resume.content_type or "application/octet-stream",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Resume upload failed")

@router.get("/resume-url/{candidate_id}")
def get_resume_signed_url(candidate_id: str, user: AuthUser = Depends(require_candidate)):
    try:
        return applicant_service.get_resume_url(candidate_id)
    except Exception as e:
        # Map not found to 404, other errors to 500
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail="Resume not found")
        raise HTTPException(status_code=500, detail="Failed to create signed URL")

@router.get("/profile")
def get_profile(request: Request, user: AuthUser = Depends(require_candidate)):
    authorization = request.headers.get("authorization", "")
    token = authorization.replace("Bearer ", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    }
    try:
        user_res = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        user_res.raise_for_status()
        user = user_res.json()
        profile = supabase.table("candidate_profiles").select("*").eq("id", user["id"]).execute()
        if not profile.data:
            raise HTTPException(status_code=404, detail="Candidate profile not found")
        return {"user": user, "profile": profile.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Profile fetch failed")

@router.get("/profile/{candidate_id}")
def get_candidate_profile(candidate_id: str):
    try:
        res = supabase.table("candidate_profiles").select("*").eq("id", candidate_id).single().execute()
        if res.error:
            raise Exception(res.error)
        return {"profile": res.data}
    except Exception:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

@router.put("/profile/{candidate_id}")
def update_candidate_profile(candidate_id: str, payload: dict, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_profiles").update(payload).eq("id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "updated", "profile": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Profile update failed")

# ---- Detailed Application Form Orchestration ----
@router.post("/detailed-form")
def save_detailed_form(payload: Dict[str, Any] = Body(...), user: AuthUser = Depends(require_candidate)):
    """
    Expected payload shape:
    {
      "candidate_id": "uuid",
      "profile": { ... minimal candidate profile fields ... },
      "education": [ { ... CandidateEducationRequest ... }, ... ],
      "experience": [ { ... CandidateExperienceRequest ... }, ... ],
      "skills": [ { ... CandidateSkillRequest ... }, ... ]
    }
    """
    try:
        candidate_id = payload.get("candidate_id")
        if not candidate_id:
            raise HTTPException(status_code=400, detail="candidate_id is required")

        applicant_service.save_detailed_form(
            candidate_id=candidate_id,
            profile=payload.get("profile") or {},
            education=payload.get("education") or [],
            experience=payload.get("experience") or [],
            skills=payload.get("skills") or [],
        )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save detailed form: {e}")


@router.get("/detailed-form/{candidate_id}")
def get_detailed_form(candidate_id: str, user: AuthUser = Depends(require_candidate)):
    try:
        return applicant_service.get_detailed_form(candidate_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed form: {e}")

# ---- General Interview Video ----
@router.post("/general-video")
async def upload_general_video(candidate_id: str = Form(...), video: UploadFile = File(...), user: AuthUser = Depends(require_candidate)):
    try:
        content = await video.read()
        result = applicant_service.upload_general_video(
            candidate_id=candidate_id,
            filename=video.filename,
            content=content,
            content_type=video.content_type or "video/mp4",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"General video upload failed: {e}")


@router.get("/general-video/{candidate_id}")
def get_general_video(candidate_id: str, user: AuthUser = Depends(require_candidate)):
    try:
        return applicant_service.get_general_video(candidate_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch general video: {e}")

@router.post("/profile/{candidate_id}/education")
def add_candidate_education(candidate_id: str, payload: CandidateEducationRequest, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_education").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "education": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add education")

@router.get("/profile/{candidate_id}/education")
def list_candidate_education(candidate_id: str, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_education").select("*").eq("candidate_id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"education": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch education")

@router.post("/profile/{candidate_id}/experience")
def add_candidate_experience(candidate_id: str, payload: CandidateExperienceRequest, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_experience").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "experience": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add experience")

@router.get("/profile/{candidate_id}/experience")
def list_candidate_experience(candidate_id: str, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_experience").select("*").eq("candidate_id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"experience": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch experience")


@router.post("/profile/{candidate_id}/skills")
def add_candidate_skill(candidate_id: str, payload: CandidateSkillRequest, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_skills").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "skill": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add skill")

@router.get("/profile/{candidate_id}/skills")
def list_candidate_skills(candidate_id: str, user: AuthUser = Depends(require_candidate)):
    try:
        res = supabase.table("candidate_skills").select("*").eq("candidate_id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"skills": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch skills")
