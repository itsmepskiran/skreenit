from typing import Optional, Dict, Any
from supabase import Client
from .supabase_client import get_client

class DashboardService:
    def __init__(self, client: Optional[Client] = None):
        self.supabase = client or get_client()

    def get_summary(self, user_id: str) -> dict:
        user_resp = self.supabase.table("users").select("role").eq("id", user_id).single().execute()
        if getattr(user_resp, "error", None) or not user_resp.data:
            raise Exception(f"User fetch error: {getattr(user_resp, 'error', 'not found')}")
        role = user_resp.data.get("role")
        summary = {"role": role, "jobs": [], "applications": []}
        if role == "recruiter":
            jobs_resp = self.supabase.table("jobs").select("id, title, status, created_at").eq("created_by", user_id).execute()
            jobs = jobs_resp.data or []
            summary["jobs"] = jobs
            job_ids = [j["id"] for j in jobs]
            if job_ids:
                apps = self.supabase.table("job_applications").select("id, status, ai_score, candidate_id, applied_at, job_id").in_("job_id", job_ids).execute()
                summary["applications"] = apps.data or []
        elif role == "candidate":
            apps = self.supabase.table("job_applications").select("id, status, ai_score, applied_at, job_id").eq("candidate_id", user_id).execute()
            applications = apps.data or []
            summary["applications"] = applications
            job_ids = [a["job_id"] for a in applications]
            jobs = self.supabase.table("jobs").select("id, title, company, location, job_type, status").in_("id", job_ids).execute()
            summary["jobs"] = jobs.data or []
        else:
            raise Exception("Unknown user role")
        return summary
