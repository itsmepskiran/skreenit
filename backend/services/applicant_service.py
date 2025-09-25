import time
from typing import Any, Dict, List, Optional, Tuple
from supabase import Client
from .supabase_client import get_client
from utils_others.file_upload import upload_to_bucket, create_signed_url

class ApplicantService:
    def __init__(self, client: Optional[Client] = None) -> None:
        self.supabase = client or get_client()

    # Detailed form orchestration
    def save_detailed_form(self, candidate_id: str, profile: Dict[str, Any] | None,
                           education: List[Dict[str, Any]] | None,
                           experience: List[Dict[str, Any]] | None,
                           skills: List[Dict[str, Any]] | None) -> None:
        if profile:
            out = {**profile}
            if "id" not in out:
                out["id"] = candidate_id
            res_prof = self.supabase.table("candidate_profiles").upsert(out, on_conflict="id").execute()
            if getattr(res_prof, "error", None):
                raise Exception(res_prof.error)
        if education:
            self.supabase.table("candidate_education").delete().eq("candidate_id", candidate_id).execute()
            to_insert = [{**e, "candidate_id": candidate_id} for e in education]
            if to_insert:
                res = self.supabase.table("candidate_education").insert(to_insert).execute()
                if getattr(res, "error", None):
                    raise Exception(res.error)
        if experience:
            self.supabase.table("candidate_experience").delete().eq("candidate_id", candidate_id).execute()
            to_insert = [{**x, "candidate_id": candidate_id} for x in experience]
            if to_insert:
                res = self.supabase.table("candidate_experience").insert(to_insert).execute()
                if getattr(res, "error", None):
                    raise Exception(res.error)
        if skills:
            self.supabase.table("candidate_skills").delete().eq("candidate_id", candidate_id).execute()
            to_insert = [{**s, "candidate_id": candidate_id} for s in skills]
            if to_insert:
                res = self.supabase.table("candidate_skills").insert(to_insert).execute()
                if getattr(res, "error", None):
                    raise Exception(res.error)

    def get_detailed_form(self, candidate_id: str) -> Dict[str, Any]:
        profile = self.supabase.table("candidate_profiles").select("*").eq("id", candidate_id).single().execute()
        education = self.supabase.table("candidate_education").select("*").eq("candidate_id", candidate_id).execute()
        experience = self.supabase.table("candidate_experience").select("*").eq("candidate_id", candidate_id).execute()
        skills = self.supabase.table("candidate_skills").select("*").eq("candidate_id", candidate_id).execute()
        return {
            "candidate_id": candidate_id,
            "profile": getattr(profile, "data", None),
            "education": getattr(education, "data", []),
            "experience": getattr(experience, "data", []),
            "skills": getattr(skills, "data", []),
        }

    # Resume upload + URL helpers
    def upload_resume(self, candidate_id: str, filename: str, content: bytes, content_type: Optional[str] = None) -> Dict[str, Any]:
        object_path = f"{candidate_id}/{int(time.time()*1000)}-{filename}"
        upload_to_bucket(self.supabase, "resumes", object_path, content, content_type or "application/pdf")
        # Persist resume_path on candidate profile (upsert)
        self.supabase.table("candidate_profiles").upsert({
            "id": candidate_id,
            "resume_path": object_path,
        }, on_conflict="id").execute()
        # Create signed URL for immediate consumption
        signed_url = create_signed_url(self.supabase, "resumes", object_path, 3600)
        return {"resume_url": signed_url, "resume_path": object_path}

    def get_resume_url(self, candidate_id: str) -> Dict[str, Any]:
        prof = self.supabase.table("candidate_profiles").select("resume_path, resume_url").eq("id", candidate_id).single().execute()
        data = getattr(prof, "data", None) or {}
        path = data.get("resume_path")
        if not path:
            url = data.get("resume_url")
            if url:
                return {"resume_url": url}
            raise Exception("Resume not found")
        try:
            signed = create_signed_url(self.supabase, "resumes", path, 3600)
            return {"resume_url": signed}
        except Exception as e:
            raise Exception("Could not generate signed URL")

    # General interview video upload + analysis
    def upload_general_video(self, candidate_id: str, filename: str, content: bytes,
                             content_type: Optional[str] = None) -> Dict[str, Any]:
        # Store video in private bucket
        object_path = f"{candidate_id}/{int(time.time()*1000)}-{filename}"
        upload_to_bucket(self.supabase, "general_videos", object_path, content, content_type or "video/mp4")

        # Placeholder analysis: compute simple heuristic scores (0-20 each). Integrate ML/API later.
        # Example signals: file size, duration (if extracted), random seeds, etc. For now static demo values.
        scores = self._analyze_video_placeholder(candidate_id, object_path, len(content))

        rec = {
            "candidate_id": candidate_id,
            "video_path": object_path,
            "video_url": None,
            "status": "completed",
            "scores": scores,
        }
        self.supabase.table("general_videos").insert(rec).execute()
        return {"ok": True, "status": "completed", "scores": scores}

    def get_general_video(self, candidate_id: str) -> Dict[str, Any]:
        res = self.supabase.table("general_videos").select("*") \
            .eq("candidate_id", candidate_id).order("created_at", desc=True).limit(1).execute()
        items = getattr(res, "data", []) or []
        if not items:
            return {"status": "missing"}
        item = items[0]
        signed_url = None
        try:
            fp = item.get("video_path")
            if fp:
                signed_url = create_signed_url(self.supabase, "general_videos", fp, 3600)
        except Exception:
            signed_url = None
        return {
            "status": item.get("status", "uploaded"),
            "video_url": signed_url,
            "scores": item.get("scores"),
        }

    def _analyze_video_placeholder(self, candidate_id: str, object_path: str, size_bytes: int) -> Dict[str, int]:
        # Simple deterministic scores using hash-like arithmetic for demo purposes
        base = (hash(candidate_id) ^ hash(object_path) ^ size_bytes) & 0xFFFF
        def norm(v):
            return max(10, min(20, 10 + (v % 11)))
        return {
            "communication": norm(base // 7),
            "appearance": norm(base // 11),
            "attitude": norm(base // 13),
            "behaviour": norm(base // 17),
            "confidence": norm(base // 19),
            "total": 0,  # computed below
        } | {"total": sum([
            # total capped at 100
            min(20, 10 + ((base // 7) % 11)),
            min(20, 10 + ((base // 11) % 11)),
            min(20, 10 + ((base // 13) % 11)),
            min(20, 10 + ((base // 17) % 11)),
            min(20, 10 + ((base // 19) % 11)),
        ])}
