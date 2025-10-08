from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client, Client
from typing import Optional
from models.dashboard_models import DashboardSummary
import os

router = APIRouter(tags=["dashboard"])

# Utility for Supabase client (adjust import as per your project)
def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials are not set")
    return create_client(supabase_url, supabase_key)

@router.get("/summary/{user_id}")
def get_dashboard_summary(user_id: str, client: Client = Depends(get_supabase_client)):
    """
    Provides a dashboard summary highly specific to the user's role.
    E.g., jobs posted, applications, or relevant analytics.
    """
    # This is a sample implementation—you should tailor logic to your needs.
    user_resp = client.table("users").select("role").eq("id", user_id).single().execute()
    if getattr(user_resp, "error", None):
        raise HTTPException(status_code=404, detail="User not found")
    role = user_resp.data.get("role")

    summary = {"role": role, "jobs": [], "applications": []}

    if role == "recruiter":
        jobs_resp = client.table("jobs").select("*").eq("created_by", user_id).execute()
        summary["jobs"] = jobs_resp.data if getattr(jobs_resp, "data", None) else []

        applications_resp = client.table("job_applications").select("*").in_("job_id", [job["id"] for job in summary["jobs"]]).execute()
        summary["applications"] = applications_resp.data if getattr(applications_resp, "data", None) else []

    elif role == "candidate":
        applications_resp = client.table("job_applications").select("*").eq("candidate_id", user_id).execute()
        summary["applications"] = applications_resp.data if getattr(applications_resp, "data", None) else []

        jobs_applied = [app["job_id"] for app in summary["applications"]]
        jobs_resp = client.table("jobs").select("*").in_("id", jobs_applied).execute()
        summary["jobs"] = jobs_resp.data if getattr(jobs_resp, "data", None) else []

    else:
        raise HTTPException(status_code=400, detail="Unknown user role")

    return DashboardSummary(**summary)
