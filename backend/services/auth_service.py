import os
import httpx
from typing import Optional, Dict, Any
from supabase import Client
from .supabase_client import get_client
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

        login_url = os.getenv("FRONTEND_BASE_URL", "https://login.skreenit.com")
        html = f"""
        <div>
          <p>Hi {full_name},</p>
          <p>Welcome to Skreenit! Your account has been created.</p>
          <p><strong>Login Email:</strong> {email}<br/>
          <strong>Temporary Password:</strong> {temp_password}</p>
          <p>Please login and change your password:</p>
          <p><a href=\"{login_url}\">{login_url}</a></p>
          <p>Regards,<br/>Skreenit Team</p>
        </div>
        """
        try:
            email_res = send_email(to=email, subject="Welcome to Skreenit - Your Account Details", html=html)
        except Exception as e:
            email_res = {"error": str(e)}

        return {
            "ok": True,
            "user_id": user_id,
            "resume_path": resume_path,
            "email": email,
            "email_sent": "error" not in email_res,
            "email_response": str(email_res),
        }

    def notify_password_changed(self, email: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        display_name = full_name or (email.split("@")[0])
        html = f"""
        <div>
          <p>Hi {display_name},</p>
          <p>Your Skreenit account password was updated successfully.</p>
          <p>If you did not initiate this change, please contact support immediately.</p>
          <p>Regards,<br/>Skreenit Team</p>
        </div>
        """
        try:
            res = send_email(to=email, subject="Skreenit Password Updated", html=html)
            return {"email_sent": True, "response": res}
        except Exception as e:
            return {"email_sent": False, "error": str(e)}
