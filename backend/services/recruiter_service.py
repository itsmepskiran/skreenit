from typing import Optional, List, Dict, Any
from supabase import Client
from .supabase_client import get_client

class RecruiterService:
    def __init__(self, client: Optional[Client] = None):
        self.supabase = client or get_client()

    def post_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.supabase.table("jobs").insert(job_data).execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Job post error: {err}")
        return {"status": "posted", "data": res.data}

    def list_jobs(self) -> List[Dict[str, Any]]:
        res = self.supabase.table("jobs").select("*").execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Job list error: {err}")
        return res.data

    def get_job(self, job_id: str) -> Dict[str, Any]:
        res = self.supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Get job error: {err}")
        return res.data

    def update_job(self, job_id: str, update_data: Dict[str, Any], recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        query = self.supabase.table("jobs").update(update_data).eq("id", job_id)
        if recruiter_id:
            query = query.eq("created_by", recruiter_id)
        res = query.execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Update job error: {err}")
        return {"ok": True, "data": res.data}

    def delete_job(self, job_id: str, recruiter_id: Optional[str] = None) -> Dict[str, Any]:
        query = self.supabase.table("jobs").delete().eq("id", job_id)
        if recruiter_id:
            query = query.eq("created_by", recruiter_id)
        res = query.execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Delete job error: {err}")
        return {"ok": True, "data": res.data}

    def list_companies(self) -> List[Dict[str, Any]]:
        res = self.supabase.table("companies").select("id,name,website").order("name").execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Company list error: {err}")
        return res.data

    def create_company(self, name: str, created_by: str, description: Optional[str] = None, website: Optional[str] = None) -> Dict[str, Any]:
        import random, string
        base = ''.join(ch for ch in name if ch.isalpha()).upper()
        if len(base) < 8:
            base = base + ''.join(random.choice(string.ascii_uppercase) for _ in range(8 - len(base)))
        company_id = base[:8]
        payload = {
            "id": company_id,
            "name": name,
            "description": description,
            "website": website,
            "created_by": created_by,
        }
        res = self.supabase.table("companies").insert(payload).execute()
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Create company error: {err}")
        return {"company_id": company_id, "company": res.data}

    def upsert_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("user_id"):
            raise Exception("user_id is required")
        res = (
            self.supabase
            .table("recruiter_profiles")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
        err = getattr(res, "error", None)
        if err:
            raise Exception(f"Upsert recruiter profile error: {err}")
        # Mark recruiter onboarded in router (done there), or here if you prefer:
        # try:
        #     self.supabase.auth.admin.update_user_by_id(payload["user_id"], {"user_metadata": {"onboarded": True}})
        # except Exception:
        #     pass
        return {"status": "saved", "profile": res.data}
