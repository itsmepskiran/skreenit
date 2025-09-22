from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from models.recruiter_models import JobPostRequest
from models.recruiter_models import JobSkillRequest

router = APIRouter(tags=["recruiter"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.post("/post-job")
def post_job(payload: JobPostRequest):
    try:
        res = supabase.table("jobs").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "posted", "data": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Job post failed")

@router.get("/jobs")
def list_jobs():
    try:
        res = supabase.table("jobs").select("*").execute()
        if res.error:
            raise Exception(res.error)
        return {"jobs": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not fetch jobs")

@router.get("/job/{job_id}")
def get_job(job_id: str):
    try:
        res = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        if res.error:
            raise Exception(res.error)
        return {"job": res.data}
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

@router.put("/job/{job_id}")
def update_job(job_id: str, payload: JobPostRequest):
    try:
        res = supabase.table("jobs").update(payload.dict(exclude_unset=True)).eq("id", job_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "updated", "job": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Job update failed")

@router.delete("/job/{job_id}")
def delete_job(job_id: str):
    try:
        res = supabase.table("jobs").delete().eq("id", job_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "deleted"}
    except Exception:
        raise HTTPException(status_code=500, detail="Job delete failed")

@router.get("/companies")
def list_companies():
    try:
        res = supabase.table("companies").select("*").execute()
        if res.error:
            raise Exception(res.error)
        return {"companies": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not fetch companies")

@router.get("/job/{job_id}/applications")
def list_job_applications(job_id: str):
    try:
        res = supabase.table("job_applications").select("*").eq("job_id", job_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"applications": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not fetch applications")

@router.get("/applicants")
def list_applicants(company_id: str):
    try:
        res = supabase.table("job_applications").select("*").eq("company_id", company_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "fetched", "applicants": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Applicant fetch failed")

@router.post("/job/{job_id}/skills")
def add_job_skill(job_id: str, payload: JobSkillRequest):
    try:
        res = supabase.table("job_skills").insert(payload.dict()).execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "added", "skill": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add skill")

@router.get("/job/{job_id}/skills")
def list_job_skills(job_id: str):
    try:
        res = supabase.table("job_skills").select("*").eq("job_id", job_id).execute()
        if res.error:
            raise Exception(res.error)
        return {"skills": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch skills")
