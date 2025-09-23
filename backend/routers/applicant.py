from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request
from fastapi import Body
from supabase import create_client, Client
import os, secrets, httpx
from typing import Any, Dict, List, Optional
from models.applicant_models import ApplicationRequest
from models.applicant_models import CandidateEducationRequest
from models.applicant_models import CandidateExperienceRequest
from models.applicant_models import CandidateSkillRequest

router = APIRouter(tags=["applicant"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.post("/apply")
def apply_job(payload: ApplicationRequest):
    try:
        res = supabase.table("job_applications").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "applied", "data": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Application failed")

@router.post("/upload-resume")
async def upload_resume(applicant_id: str = Form(...), resume: UploadFile = File(...)):
    try:
        file_bytes = await resume.read()
        path = f"{applicant_id}/{secrets.token_hex(4)}-{resume.filename}"
        up = supabase.storage.from_("resumes").upload(path, file_bytes, {
            "contentType": resume.content_type or "application/octet-stream"
        })
        if getattr(up, "error", None):
            raise Exception(up.error)

        # Persist resume_path on candidate profile if exists
        try:
            supabase.table("candidate_profiles").upsert({
                "id": applicant_id,
                "resume_path": path
            }, on_conflict="id").execute()
        except Exception:
            pass

        # Create a short-lived signed URL for immediate consumption
        signed = supabase.storage.from_("resumes").create_signed_url(path, 3600)
        signed_url = (signed or {}).get("data", {}).get("signedUrl")
        return {"resume_url": signed_url, "resume_path": path}
    except Exception:
        raise HTTPException(status_code=500, detail="Resume upload failed")

@router.get("/resume-url/{candidate_id}")
def get_resume_signed_url(candidate_id: str):
    try:
        prof = supabase.table("candidate_profiles").select("resume_path, resume_url").eq("id", candidate_id).single().execute()
        data = getattr(prof, "data", None) or {}
        path = data.get("resume_path")
        if not path:
            # Backward compatibility: if only a public URL was stored historically, return it as-is
            url = data.get("resume_url")
            if url:
                return {"resume_url": url}
            raise HTTPException(status_code=404, detail="Resume not found")
        signed = supabase.storage.from_("resumes").create_signed_url(path, 3600)
        signed_url = (signed or {}).get("data", {}).get("signedUrl")
        if not signed_url:
            raise HTTPException(status_code=500, detail="Could not generate signed URL")
        return {"resume_url": signed_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create signed URL: {e}")

@router.get("/profile")
def get_profile(request: Request):
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
def update_candidate_profile(candidate_id: str, payload: dict):
    try:
        res = supabase.table("candidate_profiles").update(payload).eq("id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "updated", "profile": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Profile update failed")

# ---- Detailed Application Form Orchestration ----
@router.post("/detailed-form")
def save_detailed_form(payload: Dict[str, Any] = Body(...)):
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

        # Upsert profile if provided
        profile_data = payload.get("profile") or {}
        if profile_data:
            # Ensure id key matches schema expectations
            profile_data_out = {**profile_data}
            # Many schemas use id as PK; fall back to user_id field
            if "id" not in profile_data_out:
                profile_data_out["id"] = candidate_id
            res_prof = supabase.table("candidate_profiles").upsert(profile_data_out, on_conflict="id").execute()
            if getattr(res_prof, "error", None):
                raise Exception(res_prof.error)

        # Replace education
        educ_list: List[Dict[str, Any]] = payload.get("education") or []
        if educ_list:
            # Delete existing items for candidate, then insert
            supabase.table("candidate_education").delete().eq("candidate_id", candidate_id).execute()
            to_insert = []
            for e in educ_list:
                item = {**e, "candidate_id": candidate_id}
                to_insert.append(item)
            if to_insert:
                res_edu = supabase.table("candidate_education").insert(to_insert).execute()
                if getattr(res_edu, "error", None):
                    raise Exception(res_edu.error)

        # Replace experience
        exp_list: List[Dict[str, Any]] = payload.get("experience") or []
        if exp_list:
            supabase.table("candidate_experience").delete().eq("candidate_id", candidate_id).execute()
            to_insert = []
            for x in exp_list:
                item = {**x, "candidate_id": candidate_id}
                to_insert.append(item)
            if to_insert:
                res_exp = supabase.table("candidate_experience").insert(to_insert).execute()
                if getattr(res_exp, "error", None):
                    raise Exception(res_exp.error)

        # Replace skills
        skills_list: List[Dict[str, Any]] = payload.get("skills") or []
        if skills_list:
            supabase.table("candidate_skills").delete().eq("candidate_id", candidate_id).execute()
            to_insert = []
            for s in skills_list:
                item = {**s, "candidate_id": candidate_id}
                to_insert.append(item)
            if to_insert:
                res_sk = supabase.table("candidate_skills").insert(to_insert).execute()
                if getattr(res_sk, "error", None):
                    raise Exception(res_sk.error)

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save detailed form: {e}")


@router.get("/detailed-form/{candidate_id}")
def get_detailed_form(candidate_id: str):
    try:
        profile = supabase.table("candidate_profiles").select("*").eq("id", candidate_id).single().execute()
        education = supabase.table("candidate_education").select("*").eq("candidate_id", candidate_id).execute()
        experience = supabase.table("candidate_experience").select("*").eq("candidate_id", candidate_id).execute()
        skills = supabase.table("candidate_skills").select("*").eq("candidate_id", candidate_id).execute()
        return {
            "candidate_id": candidate_id,
            "profile": getattr(profile, "data", None),
            "education": getattr(education, "data", []),
            "experience": getattr(experience, "data", []),
            "skills": getattr(skills, "data", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed form: {e}")

# ---- General Interview Video ----
@router.post("/general-video")
async def upload_general_video(candidate_id: str = Form(...), video: UploadFile = File(...)):
    try:
        content = await video.read()
        path = f"{candidate_id}/{secrets.token_hex(6)}-{video.filename}"
        up = supabase.storage.from_("general_videos").upload(path, content, {
            "contentType": video.content_type or "video/mp4"
        })
        if getattr(up, "error", None):
            raise Exception(up.error)
        # Persist metadata in a table (assumes table general_videos exists). For private bucket, do not store public URL.
        # Placeholder analysis: mark as completed with dummy scores
        scores = {
            "communication": 18,
            "appearance": 19,
            "attitude": 20,
            "behaviour": 19,
            "confidence": 20,
            "total": 96
        }
        rec = {
            "candidate_id": candidate_id,
            "video_path": path,
            "video_url": None,
            "status": "completed",
            "scores": scores,
        }
        supabase.table("general_videos").insert(rec).execute()
        return {"ok": True, "status": "completed", "scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"General video upload failed: {e}")


@router.get("/general-video/{candidate_id}")
def get_general_video(candidate_id: str):
    try:
        res = supabase.table("general_videos").select("*").eq("candidate_id", candidate_id).order("created_at", desc=True).limit(1).execute()
        items = getattr(res, "data", []) or []
        if not items:
            return {"status": "missing"}
        item = items[0]
        # Generate a signed URL valid for 1 hour if path exists
        signed_url = None
        try:
            file_path = item.get("video_path")
            if file_path:
                su = supabase.storage.from_("general_videos").create_signed_url(file_path, 3600)
                signed_url = (su or {}).get("data", {}).get("signedUrl")
        except Exception:
            signed_url = None
        return {
            "status": item.get("status", "uploaded"),
            "video_url": signed_url,
            "scores": item.get("scores"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch general video: {e}")

@router.post("/profile/{candidate_id}/education")
def add_candidate_education(candidate_id: str, payload: CandidateEducationRequest):
    try:
        res = supabase.table("candidate_education").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "education": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add education")

@router.get("/profile/{candidate_id}/education")
def list_candidate_education(candidate_id: str):
    try:
        res = supabase.table("candidate_education").select("*").eq("candidate_id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"education": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch education")

@router.post("/profile/{candidate_id}/experience")
def add_candidate_experience(candidate_id: str, payload: CandidateExperienceRequest):
    try:
        res = supabase.table("candidate_experience").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "experience": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add experience")

@router.get("/profile/{candidate_id}/experience")
def list_candidate_experience(candidate_id: str):
    try:
        res = supabase.table("candidate_experience").select("*").eq("candidate_id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"experience": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch experience")


@router.post("/profile/{candidate_id}/skills")
def add_candidate_skill(candidate_id: str, payload: CandidateSkillRequest):
    try:
        res = supabase.table("candidate_skills").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "skill": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add skill")

@router.get("/profile/{candidate_id}/skills")
def list_candidate_skills(candidate_id: str):
    try:
        res = supabase.table("candidate_skills").select("*").eq("candidate_id", candidate_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"skills": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch skills")
