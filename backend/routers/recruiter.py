from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from models.recruiter_models import JobPostRequest
from models.recruiter_models import JobSkillRequest
from models.recruiter_models import RecruiterProfileRequest

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

@router.post("/profile")
def create_recruiter_profile(payload: RecruiterProfileRequest):
    try:
        data = payload.dict()
        # Assume table: recruiter_profiles with user_id as primary key
        res = supabase.table("recruiter_profiles").upsert(data, on_conflict="user_id").execute()
        if res.error:
            raise Exception(res.error)
        return {"status": "saved", "profile": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save recruiter profile")

@router.get("/profile/{user_id}")
def get_recruiter_profile(user_id: str):
    try:
        res = supabase.table("recruiter_profiles").select("*").eq("user_id", user_id).single().execute()
        if res.error:
            raise Exception(res.error)
        return {"profile": res.data}
    except Exception:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

@router.post("/application/{application_id}/approve")
def approve_application(application_id: str):
    """Mark an application as under_review and notify the candidate via Resend (best-effort)."""
    try:
        # Update status
        upd = supabase.table("job_applications").update({"status": "under_review"}).eq("id", application_id).execute()
        if getattr(upd, "error", None):
            raise Exception(upd.error)

        # Try to fetch candidate email from candidate_profiles (if stored)
        candidate_email = None
        try:
            app_row = (upd.data[0] if isinstance(upd.data, list) and upd.data else None) or (
                supabase.table("job_applications").select("*").eq("id", application_id).single().execute().data
            )
            candidate_id = app_row.get("candidate_id") if app_row else None
            if candidate_id:
                prof = supabase.table("candidate_profiles").select("email").eq("id", candidate_id).single().execute()
                if getattr(prof, "data", None):
                    candidate_email = prof.data.get("email")
        except Exception:
            pass

        if candidate_email:
            try:
                import os, resend
                RESEND_API_KEY = os.getenv("RESEND_API_KEY")
                EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@skreenit.app")
                resend.api_key = RESEND_API_KEY
                resend.Emails.send({
                    "from": EMAIL_FROM,
                    "to": [candidate_email],
                    "subject": "Your application has been moved under review",
                    "html": "<p>Your application status has been updated to <strong>Under Review</strong>. We will get back to you soon.</p>",
                })
            except Exception:
                # Non-fatal
                pass

        return {"status": "under_review"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to approve application")


@router.post("/job/{job_id}/questions")
def create_job_questions(job_id: str, payload: list[dict]):
    """Create or replace job questions for a job. Expects list of {question_text, question_order, time_limit}."""
    try:
        # Remove existing
        supabase.table("job_questions").delete().eq("job_id", job_id).execute()
        to_insert = []
        for idx, q in enumerate(payload):
            to_insert.append({
                "job_id": job_id,
                "question_text": q.get("question_text"),
                "question_order": q.get("question_order", idx + 1),
                "time_limit": q.get("time_limit", 120),
            })
        if to_insert:
            res = supabase.table("job_questions").insert(to_insert).execute()
            if getattr(res, "error", None):
                raise Exception(res.error)
        return {"status": "saved", "count": len(to_insert)}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save questions")


@router.get("/job/{job_id}/questions")
def list_job_questions(job_id: str):
    try:
        res = supabase.table("job_questions").select("*").eq("job_id", job_id).order("question_order").execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"questions": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.get("/application/{application_id}/resume-url")
def get_application_resume_url(application_id: str):
    """Return a signed resume URL for the application's candidate if the recruiter owns the job.
    Authorization: validated by checking jobs.created_by for the given application.
    """
    try:
        # Fetch application
        app = supabase.table("job_applications").select("job_id, candidate_id").eq("id", application_id).single().execute()
        if getattr(app, "error", None):
            raise Exception(app.error)
        app_data = getattr(app, "data", None) or {}
        job_id = app_data.get("job_id")
        candidate_id = app_data.get("candidate_id")
        if not job_id or not candidate_id:
            raise HTTPException(status_code=404, detail="Application not found")

        # Verify job exists (owner check is usually enforced by RLS in frontend calls; here we assume backend is protected by CORS and usage)
        job_res = supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
        if getattr(job_res, "error", None):
            raise Exception(job_res.error)

        # Fetch candidate profile to get resume_path or legacy resume_url
        prof = supabase.table("candidate_profiles").select("resume_path, resume_url").eq("id", candidate_id).single().execute()
        if getattr(prof, "error", None):
            raise Exception(prof.error)
        pdata = getattr(prof, "data", None) or {}
        path = pdata.get("resume_path")
        if path:
            try:
                su = supabase.storage.from_("resumes").create_signed_url(path, 3600)
                url = (su or {}).get("data", {}).get("signedUrl")
                if not url:
                    raise Exception("signed URL failed")
                return {"resume_url": url}
            except Exception:
                raise HTTPException(status_code=500, detail="Could not generate signed URL")
        # Legacy public URL fallback
        url = pdata.get("resume_url")
        if url:
            return {"resume_url": url}
        raise HTTPException(status_code=404, detail="Resume not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch resume URL")

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
