from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request
from supabase import create_client, Client
import os, secrets, httpx
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
        upload = supabase.storage.from_("resumes").upload(path, file_bytes, {
            "contentType": resume.content_type or "application/octet-stream"
        })
        public_url = supabase.storage.from_("resumes").get_public_url(path).get("data", {}).get("publicUrl")
        return {"resume_url": public_url}
    except Exception:
        raise HTTPException(status_code=500, detail="Resume upload failed")

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
