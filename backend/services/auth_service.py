import os
import httpx
from typing import Optional, Dict, Any
from supabase import Client
from services.supabase_client import get_client
from utils_others.resend_email import send_email

class AuthService:
    def __init__(self, client: Optional[Client] = None) -> None:
        self.supabase = client or get_client()
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    def login(self, email: str, password: str) -> Dict[str, Any]:
        res = self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if not getattr(res, "session", None):
            raise ValueError("Invalid credentials")
        return {"access_token": res.session.access_token, "user": res.user}

    def validate_token(self, bearer_token: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "apikey": self.service_key or "",
        }
        resp = httpx.get(f"{self.supabase_url}/auth/v1/user", headers=headers)
        resp.raise_for_status()
        return {"user": resp.json()}

    def register(self,
                 full_name: str,
                 email: str,
                 mobile: str,
                 location: str,
                 role: str,
                 company_id: Optional[str] = None,
                 company_name: Optional[str] = None,
                 resume_bytes: Optional[bytes] = None,
                 resume_filename: Optional[str] = None) -> Dict[str, Any]:
        import secrets, time

        ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"
        def gen_temp(length: int = 12) -> str:
            return "".join(secrets.choice(ALPHABET) for _ in range(length))

        temp_password = gen_temp(12)
        try:
            auth_res = self.supabase.auth.admin.create_user({
                "email": email,
                "password": temp_password,
                # Enable Supabase email confirmation
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "mobile": mobile,
                    "location": location,
                    "role": role,
                    "first_login": True,
                    **({"company_id": company_id} if company_id else {}),
                },
            })
        except Exception as ce:
            msg = str(ce)
            if "User already registered" in msg or "already exists" in msg:
                raise ValueError("User already registered")
            raise

        user = getattr(auth_res, "user", None)
        user_id = user.id if user else None
        if not user_id:
            raise RuntimeError("Failed to create user in Supabase")

        resume_path = None
        if resume_bytes is not None and resume_filename:
            try:
                ts = int(time.time() * 1000)
                safe_name = resume_filename.replace(" ", "_")
                resume_path = f"{user_id}/{ts}-{safe_name}"
                up = self.supabase.storage.from_("resumes").upload(resume_path, resume_bytes)
                if getattr(up, "error", None):
                    # non-fatal
                    resume_path = None
            except Exception:
                resume_path = None

        # If recruiter and company_name provided but company_id missing, create company and update user metadata
        final_company_id = company_id
        if role == "recruiter" and (not final_company_id) and (company_name or "").strip():
            import random, string
            base = ''.join(ch for ch in (company_name or "") if ch.isalpha()).upper()
            base = (base[:8] if len(base) >= 8 else base + ''.join(random.choice(string.ascii_uppercase) for _ in range(8 - len(base)))) or 'COMPANYID'
            gen_id = base[:8]
            try:
                comp_ins = self.supabase.table("companies").insert({
                    "id": gen_id,
                    "name": company_name,
                    "created_by": user_id,
                }).execute()
                if getattr(comp_ins, "error", None):
                    raise Exception(comp_ins.error)
                final_company_id = gen_id
                # update user metadata with company_id
                try:
                    _ = self.supabase.auth.admin.update_user_by_id(user_id, {"user_metadata": {"company_id": final_company_id}})
                except Exception:
                    pass
            except Exception:
                # fall back to no company id if insert fails
                final_company_id = None

        login_url = os.getenv("FRONTEND_BASE_URL", "https://login.skreenit.com")
        html = f"""
        <div>
          <p>Hi {full_name},</p>
          <p>Welcome to Skreenit! Your account has been created successfully.</p>
          <p><strong>Login Email:</strong> {email}</p>
          {('<p><strong>Your Company ID:</strong> ' + final_company_id + '</p>') if (role == 'recruiter' and final_company_id) else ''}
          <p>We've sent a confirmation email to your address. Please check your inbox (and spam folder) and click the confirmation link to activate your account.</p>
          <p>Once your email is confirmed, you can login here:</p>
          <p><a href=\"{login_url}\">{login_url}</a></p>
          <p><b>Regards,</b><br/>Team Skreenit</p>
        </div>
        """
        try:
            email_res = send_email(to=email, subject="Welcome to Skreenit", html=html)
        except Exception as e:
            email_res = {"error": str(e)}

        return {
            "ok": True,
            "user_id": user_id,
            "resume_path": resume_path,
            "email": email,
            "company_id": final_company_id,
            "email_sent": "error" not in email_res,
            "email_response": str(email_res),
        }

    def notify_password_changed(self, email: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        display_name = full_name or (email.split("@")[0])
        html = f"""
        <div>
          <p>Hi {full_name},</p>
          <p>Your Skreenit account password was updated successfully.</p>
          <p>If you did not initiate this change, please contact support immediately.</p>
          <p><b>Regards,</b><br/>Team Skreenit</p>
        </div>
        """
        try:
            res = send_email(to=email, subject="Skreenit Password Updated", html=html)
            return {"email_sent": True, "response": res}
        except Exception as e:
            return {"email_sent": False, "error": str(e)}

    def get_recruiter_company_info(self, user_id: str) -> Dict[str, Any]:
        # Try recruiter_profiles first
        prof = self.supabase.table("recruiter_profiles").select("company_id").eq("user_id", user_id).single().execute()
        company_id = None
        if getattr(prof, "data", None) and prof.data:
            company_id = prof.data.get("company_id")
        # Fallback to public auth user metadata if needed (admin API)
        if not company_id:
            try:
                user = self.supabase.auth.admin.get_user_by_id(user_id)
                meta = getattr(user, "user", None).user_metadata if getattr(user, "user", None) else {}
                company_id = meta.get("company_id") if isinstance(meta, dict) else None
            except Exception:
                company_id = None
        if not company_id:
            return {"company_id": None, "company_name": None}
        comp = self.supabase.table("companies").select("id,name").eq("id", company_id).single().execute()
        name = comp.data.get("name") if getattr(comp, "data", None) else None
        return {"company_id": company_id, "company_name": name}

    def send_recruiter_company_email(self, email: str, full_name: Optional[str], company_id: str, company_name: Optional[str]) -> Dict[str, Any]:
        cname = company_name or "Your Company"
        html = f"""
        <div>
          <p>Hi {full_name or ''},</p>
          <p>Your recruiter profile has been set up on Skreenit.</p>
          <p><strong>Company Name:</strong> {cname}<br/>
          <strong>Company ID:</strong> {company_id}</p>
          <p>Use this Company ID when logging in as a recruiter.</p>
          <p><b>Regards,</b><br/>Team Skreenit</p>
        </div>
        """
        try:
            res = send_email(to=email, subject="Your Skreenit Company ID", html=html)
            return {"email_sent": True, "response": res}
        except Exception as e:
            return {"email_sent": False, "error": str(e)}
