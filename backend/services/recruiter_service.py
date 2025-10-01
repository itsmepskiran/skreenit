from typing import Optional, List, Dict, Any
from supabase import Client
from .supabase_client import get_client

class RecruiterService:
    def __init__(self, client: Optional[Client] = None):
        self.supabase = client or get_client()

    def post_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.supabase.table("jobs").insert(job_data).execute()
        if getattr(res, "error", None):
            raise Exception(f"Job post error: {res.error}")
        return {"status": "posted", "data": res.data}

    def list_jobs(self) -> List[Dict[str, Any]]:
        res = self.supabase.table("jobs").select("*").execute()
        if getattr(res, "error", None):
            raise Exception(f"Job list error: {res.error}")
        return res.data

    def get_job(self, job_id: str) -> Dict[str, Any]:
        res = self.supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        if getattr(res, "error", None):
            raise Exception(f"Get job error: {res.error}")
        return res.data

    def update_job(self, job_id: str, update_data: Dict[str, Any], recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        # Optional: Add permission logic to ensure recruiter_id can edit job
        res = self.supabase.table("jobs").update(update_data).eq("id", job_id).execute()
        if getattr(res, "error", None):
            raise Exception(f"Update job error: {res.error}")
        return res.data

    def delete_job(self, job_id: str) -> Dict[str, Any]:
        res = self.supabase.table("jobs").delete().eq("id", job_id).execute()
        if getattr(res, "error", None):
            raise Exception(f"Delete job error: {res.error}")
        return res.data

    # Add methods for company, interview questions, and skills as needed

    def list_companies(self) -> List[Dict[str, Any]]:
        res = self.supabase.table("companies").select("id,name,website").order("name").execute()
        if getattr(res, "error", None):
            raise Exception(f"Company list error: {res.error}")
        return res.data

    def create_company(self, name: str, created_by: str, description: Optional[str] = None, website: Optional[str] = None) -> Dict[str, Any]:
        import random, string
        base = ''.join(ch for ch in name if ch.isalpha()).upper()
        base = (base[:8] if len(base) >= 8 else base + ''.join(random.choice(string.ascii_uppercase) for _ in range(8 - len(base)))) or 'COMPANYID'
        company_id = base[:8]
        payload = {
            "id": company_id,
            "name": name,
            "description": description,
            "website": website,
            "created_by": created_by,
        }
        res = self.supabase.table("companies").insert(payload).execute()
        if getattr(res, "error", None):
            raise Exception(f"Create company error: {res.error}")
        return {"company_id": company_id, "company": res.data}

    def upsert_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Expected keys: user_id, company_id, fullname, email, phone?, position?, linkedin_url?
        # Upsert on user_id
        if not payload.get("user_id"):
            raise Exception("user_id is required")
        res = (
            self.supabase
            .table("recruiter_profiles")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
        if getattr(res, "error", None):
            raise Exception(f"Upsert recruiter profile error: {res.error}")
        return {"status": "saved", "profile": res.data}
