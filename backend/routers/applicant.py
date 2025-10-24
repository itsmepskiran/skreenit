from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request, Header, Depends, Body
import os, httpx
from typing import Any, Dict, List, Optional
from services.supabase_client import get_client

from models.applicant_models import (
    ApplicationRequest,
)
from services.applicant_service import ApplicantService
from utils_others.security import get_user_from_bearer, ensure_role

router = APIRouter(tags=["applicant"])

_supabase = None
_applicant_service = None

def get_supabase():
    global _supabase
    if _supabase is None:
        try:
            _supabase = get_client()
        except Exception as e:
            raise RuntimeError("Supabase client not configured: " + str(e)) from e
    return _supabase

def get_applicant_service():
    global _applicant_service
    if _applicant_service is None:
        supabase = get_supabase()
        _applicant_service = ApplicantService(supabase)
    return _applicant_service

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

@router.post("/apply")
def apply_job(payload: ApplicationRequest, user: dict = Depends(require_candidate)):
    try:
        data = payload.dict()
        data["candidate_id"] = user["id"]
        applicant_service = get_applicant_service()
        video_info = applicant_service.get_general_video(user["id"])
        status = "submitted"
        if not video_info or video_info.get("status") == "missing":
            status = "video_pending"
        ai_analysis = data.get("ai_analysis") or {}
        if video_info and video_info.get("scores"):
            ai_analysis = {**ai_analysis, "general_video_scores": video_info.get("scores")}
        insert_payload = {
            **data,
            "status": status,
            "ai_analysis": ai_analysis or None,
        }
        supabase = get_supabase()
        res = supabase.table("job_applications").insert(insert_payload).execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(err)
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")

@router.post("/upload-resume")
async def upload_resume(applicant_id: str = Form(...), resume: UploadFile = File(...), user: dict = Depends(require_candidate)):
    try:
        content = await resume.read()
        applicant_service = get_applicant_service()
        return applicant_service.upload_resume(
            candidate_id=applicant_id,
            filename=str(resume.filename or "resume.pdf"),
            content=content,
            content_type=resume.content_type or "application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume upload failed: {str(e)}")

@router.get("/resume-url/{candidate_id}")
def get_resume_signed_url(candidate_id: str, user: dict = Depends(require_candidate)):
    try:
        applicant_service = get_applicant_service()
        return applicant_service.get_resume_url(candidate_id)
    except Exception as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail="Resume not found")
        raise HTTPException(status_code=500, detail="Failed to create signed URL")

@router.get("/profile")
def get_profile(request: Request, user: dict = Depends(require_candidate)):
    authorization = request.headers.get("authorization", "")
    token = authorization.replace("Bearer ", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    }
    try:
        user_res = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        user_res.raise_for_status()
        user_data = user_res.json()
        supabase = get_supabase()
        profile = supabase.table("candidate_profiles").select("*").eq("user_id", user_data["id"]).execute()
        if not profile.data:
            raise HTTPException(status_code=404, detail="Candidate profile not found")
        return {"ok": True, "data": {"user": user_data, "profile": profile.data}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile fetch failed: {str(e)}")

@router.get("/profile/{candidate_id}")
def get_candidate_profile(candidate_id: str, user: dict = Depends(require_candidate)):
    try:
        supabase = get_supabase()
        res = supabase.table("candidate_profiles").select("*").eq("user_id", candidate_id).single().execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(err)
        data = getattr(res, "data", None)
        if not data:
            return {"ok": True, "data": {"profile": {}}}
        return {"ok": True, "data": {"profile": data}}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Candidate profile not found: {str(e)}")

@router.put("/profile/{candidate_id}")
def update_candidate_profile(candidate_id: str, payload: dict, user: dict = Depends(require_candidate)):
    try:
        supabase = get_supabase()
        res = supabase.table("candidate_profiles").update(payload).eq("user_id", candidate_id).execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(err)
        data = getattr(res, "data", None)
        if not data:
            return {"ok": True, "data": {"profile": {}}}
        return {"ok": True, "data": {"profile": data}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

@router.post("/detailed-form")
def save_detailed_form(payload: Dict[str, Any] = Body(...), user: dict = Depends(require_candidate)):
    try:
        candidate_id = payload.get("candidate_id")
        if not candidate_id:
            raise HTTPException(status_code=400, detail="candidate_id is required")
        draft = payload.get('draft', False)
        if draft:
            # Save only profile subset as a draft and do not mark user as onboarded
            applicant_service = get_applicant_service()
            applicant_service.save_detailed_form(
                candidate_id=candidate_id,
                profile=payload.get('profile') or {},
                education=None,
                experience=None,
                skills=None,
            )
            return {"ok": True, "draft": True}

        # Full save
        applicant_service = get_applicant_service()
        applicant_service.save_detailed_form(
            candidate_id=candidate_id,
            profile=payload.get("profile") or {},
            education=payload.get("education") or [],
            experience=payload.get("experience") or [],
            skills=payload.get("skills") or [],
        )
        try:
            supabase = get_supabase()
            supabase.auth.admin.update_user_by_id(candidate_id, {"user_metadata": {"onboarded": True}})
        except Exception:
            pass
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save detailed form: {str(e)}")

@router.get("/detailed-form/{candidate_id}")
def get_detailed_form(candidate_id: str, user: dict = Depends(require_candidate)):
    try:
        applicant_service = get_applicant_service()
        return {"ok": True, "data": applicant_service.get_detailed_form(candidate_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed form: {str(e)}")


@router.post('/draft')
def save_draft(payload: Dict[str, Any] = Body(...), user: dict = Depends(require_candidate)):
    try:
        candidate_id = payload.get('candidate_id')
        if not candidate_id:
            raise HTTPException(status_code=400, detail='candidate_id is required')
        draft = payload.get('draft') or {}
        applicant_service = get_applicant_service()
        applicant_service.save_draft(candidate_id, draft)
        return {'ok': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to save draft: {str(e)}')


@router.get('/draft/{candidate_id}')
def get_draft(candidate_id: str, user: dict = Depends(require_candidate)):
    try:
        applicant_service = get_applicant_service()
        draft = applicant_service.get_draft(candidate_id)
        return {'ok': True, 'data': draft}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch draft: {str(e)}')
