from fastapi import APIRouter, Request, HTTPException
from supabase import create_client, Client
import os, httpx
from models.dashboard_models import DashboardSummary

router = APIRouter(tags=["dashboard"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@router.get("/summary")
def dashboard_summary(request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    }
    try:
        user_res = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        user_res.raise_for_status()
        user = user_res.json()
        role = user.get("user_metadata", {}).get("role")

        if role == "recruiter":
            jobs = supabase.table("jobs").select("*").eq("company_id", user["id"]).execute()
            return {"role": "recruiter", "jobs": jobs.data}

        elif role == "candidate":
            apps = supabase.table("job_applications").select("*").eq("candidate_id", user["id"]).execute()
            return {"role": "candidate", "applications": apps.data}

        else:
            return {"role": "unknown"}
    except Exception:
        raise HTTPException(status_code=500, detail="Dashboard fetch failed")
