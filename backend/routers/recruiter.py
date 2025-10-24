
from fastapi import APIRouter, HTTPException, Header, Depends
import os

from services.supabase_client import get_client

from models.recruiter_models import JobPostRequest, JobSkillRequest
from services.recruiter_service import RecruiterService
from utils_others.security import get_user_from_bearer, ensure_role

router = APIRouter(tags=["recruiter"])

_supabase = None
_service = None

def get_supabase():
    global _supabase
    if _supabase is None:
        try:
            _supabase = get_client()
        except Exception as e:
            raise RuntimeError("Supabase client not configured: " + str(e)) from e
    return _supabase

def get_recruiter_service():
    global _service
    if _service is None:
        _service = RecruiterService(get_supabase())
    return _service

def require_recruiter(authorization: str = Header(default=None)):
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
def post_job(payload: JobPostRequest, user: dict = Depends(require_recruiter)):
    try:
        data = payload.dict()
        data["created_by"] = user["id"]
        svc = get_recruiter_service()
        return {"ok": True, "data": svc.post_job(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job post failed: {str(e)}")

@router.get("/jobs")
def list_jobs(user: dict = Depends(require_recruiter)):
    try:
        svc = get_recruiter_service()
        return {"ok": True, "data": svc.list_jobs()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch jobs: {str(e)}")

@router.get("/job/{job_id}")
def get_job(job_id: str, user: dict = Depends(require_recruiter)):
    try:
        svc = get_recruiter_service()
        return {"ok": True, "data": svc.get_job(job_id)}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")

@router.put("/job/{job_id}")
def update_job(job_id: str, payload: JobPostRequest, user: dict = Depends(require_recruiter)):
    try:
        svc = get_recruiter_service()
        return svc.update_job(job_id, payload.dict(exclude_unset=True), recruiter_id=user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job update failed: {str(e)}")

@router.delete("/job/{job_id}")
def delete_job(job_id: str, user: dict = Depends(require_recruiter)):
    try:
        svc = get_recruiter_service()
        return svc.delete_job(job_id, recruiter_id=user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job delete failed: {str(e)}")

@router.post("/companies")
def create_company(payload: dict, user: dict = Depends(require_recruiter)):
    try:
        name = (payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
        desc = payload.get("description")
        website = payload.get("website")
        svc = get_recruiter_service()
        return {"ok": True, "data": svc.create_company(name=name, created_by=user["id"], description=desc, website=website)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@router.get("/companies")
def list_companies(user: dict = Depends(require_recruiter)):
    try:
        svc = get_recruiter_service()
        return {"ok": True, "data": svc.list_companies()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")

@router.post("/profile")
def create_recruiter_profile(payload: dict, user: dict = Depends(require_recruiter)):
    try:
        user_id = payload.get("user_id") or user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        company_id = payload.get("company_id")
        company_name = (payload.get("company_name") or "").strip()
        if not company_id and company_name:
            try:
                svc = get_recruiter_service()
                comps = svc.list_companies()
                found = next((c for c in comps if (c.get("name") or "").strip().lower() == company_name.lower()), None)
            except Exception:
                found = None
            if found:
                company_id = found.get("id") or found.get("company_id")
            else:
                created = svc.create_company(name=company_name, created_by=user_id, description=payload.get("company_description"), website=payload.get("company_website"))
                company_id = created.get("company_id")

        prof_payload = {
            "user_id": user_id,
            "company_id": company_id,
            "fullname": payload.get("contact_name") or payload.get("fullname") or "",
            "email": payload.get("contact_email") or payload.get("email") or "",
            "phone": payload.get("phone"),
            "position": payload.get("position"),
            "linkedin_url": payload.get("linkedin_url"),
        }
        svc = get_recruiter_service()
        profile = svc.upsert_profile(prof_payload)

        try:
            supabase = get_supabase()
            supabase.auth.admin.update_user_by_id(user_id, {"user_metadata": {"onboarded": True}})
        except Exception:
            pass

        return {"ok": True, "data": profile}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recruiter profile: {str(e)}")

@router.get("/profile/{user_id}")
def get_recruiter_profile(user_id: str, user: dict = Depends(require_recruiter)):
    try:
        svc = get_recruiter_service()
        return {"ok": True, "data": svc.get_profile(user_id)} if hasattr(svc, "get_profile") else {"ok": True, "data": {"user_id": user_id}}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Recruiter profile not found: {str(e)}")

@router.post("/job/{job_id}/skills")
def add_job_skill(job_id: str, payload: JobSkillRequest, user: dict = Depends(require_recruiter)):
    try:
        supabase = get_supabase()
        res = supabase.table("job_skills").insert(payload.dict()).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add skill: {str(e)}")

@router.get("/job/{job_id}/skills")
def list_job_skills(job_id: str, user: dict = Depends(require_recruiter)):
    try:
        supabase = get_supabase()
        res = supabase.table("job_skills").select("*").eq("job_id", job_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch skills: {str(e)}")
