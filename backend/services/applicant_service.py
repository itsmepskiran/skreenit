import time
from typing import Any, Dict, List, Optional
from supabase import Client
from services.supabase_client import get_client
from utils_others.file_upload import upload_to_bucket, create_signed_url

class ApplicantService:
    def __init__(self, client: Optional[Client] = None):
        self.supabase = client or get_client()

    # Draft handling: store/retrieve JSON draft payload in candidate_drafts table
    def save_draft(self, candidate_id: str, draft_payload: Dict[str, Any]) -> None:
        try:
            row = {"candidate_id": candidate_id, "draft": draft_payload}
            # Upsert draft by candidate_id
            res = self.supabase.table("candidate_drafts").upsert(row, on_conflict="candidate_id").execute()
            if getattr(res, "error", None):
                raise Exception(getattr(res, "error") or "Draft save error")
        except Exception as e:
            raise

    def get_draft(self, candidate_id: str) -> Dict[str, Any]:
        try:
            res = self.supabase.table("candidate_drafts").select("draft").eq("candidate_id", candidate_id).single().execute()
            if getattr(res, "error", None):
                return {}
            data = getattr(res, "data", None) or {}
            return data.get("draft") or {}
        except Exception:
            return {}

    def save_detailed_form(
        self,
        candidate_id: str,
        profile: Optional[Dict[str, Any]] = None,
        education: Optional[List[Dict[str, Any]]] = None,
        experience: Optional[List[Dict[str, Any]]] = None,
        skills: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if profile:
            profile["id"] = candidate_id
            profile["user_id"] = candidate_id
            res = (
                self.supabase.table("candidate_profiles")
                .upsert(profile, on_conflict="id")
                .execute()
            )
            err = getattr(res, "error", None)
            if err:
                raise Exception(f"Profile save error: {err}")

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
                err = getattr(res, "error", None)
                if err:
                    raise Exception(f"Education save error: {err}")

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
                err = getattr(res, "error", None)
                if err:
                    raise Exception(f"Experience save error: {err}")

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
                to_insert = [row for row in normalized if row.get("skill_name")]
                if to_insert:
                    res = self.supabase.table("candidate_skills").insert(to_insert).execute()
                    err = getattr(res, "error", None)
                    if err:
                        raise Exception(f"Skills save error: {err}")

    def get_detailed_form(self, candidate_id: str) -> Dict[str, Any]:
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
        safe_name = (filename or "resume").replace(" ", "_")
        path = f"{candidate_id}/{int(time.time()*1000)}-{safe_name}"
        upload_to_bucket(
            client=self.supabase,
            bucket="resumes",
            path=path,
            content=content,
            content_type=content_type or "application/octet-stream",
        )
        try:
            self.supabase.table("candidate_profiles").update({"resume_url": path}).eq(
                "id", candidate_id
            ).execute()
        except Exception:
            pass
        signed = create_signed_url(self.supabase, "resumes", path, 3600)
        return {"ok": True, "data": {"resume_path": path, "resume_url": signed}}

    def get_resume_url(self, candidate_id: str) -> Dict[str, Any]:
        try:
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
        return {"ok": True, "data": {"resume_url": url}}

    def get_general_video(self, candidate_id: str) -> Dict[str, Any]:
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
            out = {
                "status": data.get("status") or "completed",
                "video_url": data.get("video_url"),
            }
            ai = data.get("ai_analysis") or {}
            if isinstance(ai, dict) and ai:
                out["scores"] = ai.get("scores") or ai
            return out
        except Exception:
            return {"status": "missing"}
