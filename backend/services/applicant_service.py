import time
from typing import Any, Dict, List, Optional
from supabase import Client
from .supabase_client import get_client  # Assumes a factory to get a Supabase instance
from ..utils_others.file_upload import upload_to_bucket, create_signed_url


class ApplicantService:
    def __init__(self, client: Optional[Client] = None):
        self.supabase = client or get_client()

    def save_detailed_form(
        self,
        candidate_id: str,
        profile: Optional[Dict[str, Any]] = None,
        education: Optional[List[Dict[str, Any]]] = None,
        experience: Optional[List[Dict[str, Any]]] = None,
        skills: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Save/update a complete candidate profile, including related tables.
        """
        # Upsert candidate profile (use candidate_id as profile id for simplicity)
        if profile:
            profile["id"] = candidate_id
            res = (
                self.supabase.table("candidate_profiles")
                .upsert(profile, on_conflict="id")
                .execute()
            )
            if getattr(res, "error", None):
                raise Exception(f"Profile save error: {res.error}")

        # Replace education rows
        if education is not None:
            self.supabase.table("candidate_education").delete().eq(
                "candidate_id", candidate_id
            ).execute()
            if education:
                to_insert = [
                    {**e, "candidate_id": candidate_id}
                    for e in education
                ]
                res = self.supabase.table("candidate_education").insert(to_insert).execute()
                if getattr(res, "error", None):
                    raise Exception(f"Education save error: {res.error}")

        # Replace experience rows
        if experience is not None:
            self.supabase.table("candidate_experience").delete().eq(
                "candidate_id", candidate_id
            ).execute()
            if experience:
                to_insert = [
                    {**e, "candidate_id": candidate_id}
                    for e in experience
                ]
                res = self.supabase.table("candidate_experience").insert(to_insert).execute()
                if getattr(res, "error", None):
                    raise Exception(f"Experience save error: {res.error}")

        # Replace skills rows
        if skills is not None:
            self.supabase.table("candidate_skills").delete().eq(
                "candidate_id", candidate_id
            ).execute()
            if skills:
                normalized = []
                for s in skills:
                    normalized.append(
                        {
                            "candidate_id": candidate_id,
                            "skill_name": s.get("skill_name") or s.get("name"),
                            "proficiency_level": s.get("proficiency_level") or s.get("level"),
                            "years_experience": s.get("years_experience") or s.get("years") or 0,
                        }
                    )
                # filter out any with no name
                to_insert = [row for row in normalized if row.get("skill_name")]
                if to_insert:
                    res = self.supabase.table("candidate_skills").insert(to_insert).execute()
                    if getattr(res, "error", None):
                        raise Exception(f"Skills save error: {res.error}")

    def get_detailed_form(self, candidate_id: str) -> Dict[str, Any]:
        """Fetch profile with related education, experience, skills."""
        result: Dict[str, Any] = {}

        prof = (
            self.supabase.table("candidate_profiles")
            .select("*")
            .eq("id", candidate_id)
            .single()
            .execute()
        )
        result["profile"] = getattr(prof, "data", None)

        edu = (
            self.supabase.table("candidate_education")
            .select("*")
            .eq("candidate_id", candidate_id)
            .execute()
        )
        result["education"] = getattr(edu, "data", [])

        exp = (
            self.supabase.table("candidate_experience")
            .select("*")
            .eq("candidate_id", candidate_id)
            .execute()
        )
        result["experience"] = getattr(exp, "data", [])

        skl = (
            self.supabase.table("candidate_skills")
            .select("*")
            .eq("candidate_id", candidate_id)
            .execute()
        )
        result["skills"] = getattr(skl, "data", [])

        return result

    def upload_resume(
        self,
        candidate_id: str,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload resume to storage and return a signed URL reference."""
        safe_name = (filename or "resume").replace(" ", "_")
        path = f"{candidate_id}/{int(time.time()*1000)}-{safe_name}"
        upload_to_bucket(
            client=self.supabase,
            bucket="resumes",
            path=path,
            content=content,
            content_type=content_type or "application/octet-stream",
        )
        # Optionally store resume_url in candidate_profiles
        try:
            self.supabase.table("candidate_profiles").update({"resume_url": path}).eq(
                "id", candidate_id
            ).execute()
        except Exception:
            pass
        signed = create_signed_url(self.supabase, "resumes", path, 3600)
        return {"resume_path": path, "resume_url": signed}

    def get_resume_url(self, candidate_id: str) -> Dict[str, Any]:
        """Return a signed URL for the most recent resume in candidate's folder."""
        try:
            # Try profile.resume_url first if set
            prof = (
                self.supabase.table("candidate_profiles")
                .select("resume_url")
                .eq("id", candidate_id)
                .single()
                .execute()
            )
            path = getattr(prof, "data", {}) or {}
            path = path.get("resume_url")
        except Exception:
            path = None

        # If not stored, list bucket folder and pick the latest by name
        if not path:
            try:
                listing = self.supabase.storage.from_("resumes").list(candidate_id)
                files = getattr(listing, "data", []) or []
                files.sort(key=lambda f: f.get("name", ""), reverse=True)
                if files:
                    path = f"{candidate_id}/{files[0]['name']}"
            except Exception:
                path = None

        if not path:
            raise Exception("Resume not found")

        url = create_signed_url(self.supabase, "resumes", path, 3600)
        return {"resume_url": url}

    def get_general_video(self, candidate_id: str) -> Dict[str, Any]:
        """Fetch general video record if present."""
        try:
            res = (
                self.supabase.table("general_video_interviews")
                .select("*")
                .eq("candidate_id", candidate_id)
                .single()
                .execute()
            )
            if getattr(res, "error", None):
                return {"status": "missing"}
            data = getattr(res, "data", None)
            if not data:
                return {"status": "missing"}
            # Normalize response a little
            out = {
                "status": data.get("status") or "completed",
                "video_url": data.get("video_url"),
            }
            # Optional scores if stored in ai_analysis
            ai = data.get("ai_analysis") or {}
            if isinstance(ai, dict) and ai:
                out["scores"] = ai.get("scores") or ai
            return out
        except Exception:
            return {"status": "missing"}
