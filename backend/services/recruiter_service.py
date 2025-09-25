from typing import Optional, List, Dict, Any
from supabase import Client
from .supabase_client import get_client

class RecruiterService:
    def __init__(self, client: Optional[Client] = None) -> None:
        self.supabase = client or get_client()

    # Jobs CRUD
    def post_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.supabase.table("jobs").insert(data).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "posted", "data": res.data}

    def list_jobs(self) -> Dict[str, Any]:
        res = self.supabase.table("jobs").select("*").execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"jobs": res.data}

    def get_job(self, job_id: str) -> Dict[str, Any]:
        res = self.supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"job": res.data}

    def update_job(self, job_id: str, data: Dict[str, Any], recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        # Optional ownership check
        if recruiter_id:
            own = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if getattr(own, "data", None):
                if own.data.get("created_by") != recruiter_id:
                    raise PermissionError("Forbidden")
        res = self.supabase.table("jobs").update(data).eq("id", job_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "updated", "job": res.data}

    def delete_job(self, job_id: str, recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        if recruiter_id:
            own = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if getattr(own, "data", None):
                if own.data.get("created_by") != recruiter_id:
                    raise PermissionError("Forbidden")
        res = self.supabase.table("jobs").delete().eq("id", job_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "deleted"}

    # Recruiter profile
    def upsert_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.supabase.table("recruiter_profiles").upsert(data, on_conflict="user_id").execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "saved", "profile": res.data}

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        res = self.supabase.table("recruiter_profiles").select("*").eq("user_id", user_id).single().execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"profile": res.data}

    # Applications
    def approve_application(self, application_id: str, recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        # Ownership check: application -> job_id -> jobs.created_by
        if recruiter_id:
            app = self.supabase.table("job_applications").select("job_id").eq("id", application_id).single().execute()
            if not getattr(app, "data", None):
                raise Exception("Application not found")
            job_id = app.data.get("job_id")
            job = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if not getattr(job, "data", None) or job.data.get("created_by") != recruiter_id:
                raise PermissionError("Forbidden")
        upd = self.supabase.table("job_applications").update({"status": "under_review"}).eq("id", application_id).execute()
        if getattr(upd, "error", None):
            raise Exception(upd.error)

        # Notify candidate via email if email exists (best-effort)
        try:
            app_row = (upd.data[0] if isinstance(upd.data, list) and upd.data else None) or (
                self.supabase.table("job_applications").select("*").eq("id", application_id).single().execute().data
            )
            candidate_id = app_row.get("candidate_id") if app_row else None
            if candidate_id:
                prof = self.supabase.table("candidate_profiles").select("email").eq("id", candidate_id).single().execute()
                candidate_email = None
                if getattr(prof, "data", None):
                    candidate_email = prof.data.get("email")
                if candidate_email:
                    try:
                        import os
                        from utils_others.resend_email import send_email
                        EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@skreenit.app")
                        send_email(
                            to=candidate_email,
                            subject="Your application has been moved under review",
                            html=("<p>Your application status has been updated to <strong>Under Review</strong>. "
                                 "We will get back to you soon.</p>"),
                            from_addr=EMAIL_FROM,
                        )
                    except Exception:
                        pass
        except Exception:
            pass

        return {"status": "under_review"}

    def get_application_resume_url(self, application_id: str, recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        app = self.supabase.table("job_applications").select("job_id, candidate_id").eq("id", application_id).single().execute()
        if getattr(app, "error", None):
            raise Exception(app.error)
        data = getattr(app, "data", None) or {}
        job_id = data.get("job_id")
        candidate_id = data.get("candidate_id")
        if not job_id or not candidate_id:
            raise Exception("Application not found")
        # Ownership check
        if recruiter_id:
            job = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if not getattr(job, "data", None) or job.data.get("created_by") != recruiter_id:
                raise PermissionError("Forbidden")

        # Fetch candidate profile to get resume_path or legacy resume_url
        prof = self.supabase.table("candidate_profiles").select("resume_path, resume_url").eq("id", candidate_id).single().execute()
        if getattr(prof, "error", None):
            raise Exception(prof.error)
        pdata = getattr(prof, "data", None) or {}
        path = pdata.get("resume_path")
        if path:
            try:
                su = self.supabase.storage.from_("resumes").create_signed_url(path, 3600)
                url = (su or {}).get("data", {}).get("signedUrl")
                if not url:
                    raise Exception("signed URL failed")
                return {"resume_url": url}
            except Exception as e:
                raise Exception("Could not generate signed URL")
        url = pdata.get("resume_url")
        if url:
            return {"resume_url": url}
        raise Exception("Resume not found")

    # Questions
    def save_job_questions(self, job_id: str, items: List[Dict[str, Any]], recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        if recruiter_id:
            own = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if not getattr(own, "data", None) or own.data.get("created_by") != recruiter_id:
                raise PermissionError("Forbidden")
        self.supabase.table("job_questions").delete().eq("job_id", job_id).execute()
        to_insert = []
        for idx, q in enumerate(items):
            to_insert.append({
                "job_id": job_id,
                "question_text": q.get("question_text"),
                "question_order": q.get("question_order", idx + 1),
                "time_limit": q.get("time_limit", 120),
            })
        if to_insert:
            res = self.supabase.table("job_questions").insert(to_insert).execute()
            if getattr(res, "error", None):
                raise Exception(res.error)
        return {"status": "saved", "count": len(to_insert)}

    def list_job_questions(self, job_id: str, recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        if recruiter_id:
            own = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if not getattr(own, "data", None) or own.data.get("created_by") != recruiter_id:
                raise PermissionError("Forbidden")
        res = self.supabase.table("job_questions").select("*").eq("job_id", job_id).order("question_order").execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"questions": res.data}

    # Lists
    def list_companies(self) -> Dict[str, Any]:
        res = self.supabase.table("companies").select("*").execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"companies": res.data}

    def list_job_applications(self, job_id: str, recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        if recruiter_id:
            own = self.supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
            if not getattr(own, "data", None) or own.data.get("created_by") != recruiter_id:
                raise PermissionError("Forbidden")
        res = self.supabase.table("job_applications").select("*").eq("job_id", job_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"applications": res.data}

    def list_applicants(self, company_id: str) -> Dict[str, Any]:
        res = self.supabase.table("job_applications").select("*").eq("company_id", company_id).execute()
        if getattr(res, "error", None):
            raise Exception(res.error)
        return {"status": "fetched", "applicants": res.data}
