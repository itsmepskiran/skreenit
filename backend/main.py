# FastAPI backend for Skreenit auth and onboarding
# Features:
# - /auth/register: Creates Supabase auth user with temp password, uploads resume (optional), inserts profile row, sends email via Resend
# - /auth/password-changed: Sends confirmation email on password change
# - /health: Health check for Render

import os
import secrets
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from supabase import create_client, Client
from resend import Emails, Resend

# ---------- Config ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # NEVER expose on frontend
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@skreenit.app")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://login.skreenit.com")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", FRONTEND_BASE_URL).split(",")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

resend_client: Optional[Resend] = None
if RESEND_API_KEY:
    resend_client = Resend(RESEND_API_KEY)

app = FastAPI(title="Skreenit Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class RegistrationResponse(BaseModel):
    user_id: str
    email_sent: bool
    role: str
    message: str

class PasswordChangedRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class HealthResponse(BaseModel):
    status: str

# ---------- Utils ----------
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"

def generate_temp_password(length: int = 12) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

async def send_resend_email(to_email: str, subject: str, html: str) -> bool:
    if not resend_client:
        return False
    try:
        Emails(resend_client).send({
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        print("Resend email error:", e)
        return False

# ---------- Routes ----------
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")

@app.post("/auth/register", response_model=RegistrationResponse)
async def register(
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    mobile: str = Form(...),
    location: str = Form(...),
    role: str = Form(...),  # 'candidate' or 'recruiter'
    company_id: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
):
    role = role.lower()
    if role not in ("candidate", "recruiter"):
        raise HTTPException(status_code=400, detail="Invalid role; must be candidate or recruiter")
    if role == "recruiter" and not company_id:
        raise HTTPException(status_code=400, detail="company_id is required for recruiter registration")

    temp_password = generate_temp_password(12)

    # 1) Create auth user via Admin API
    try:
        res = supabase.auth.admin.create_user({
            "email": str(email),
            "password": temp_password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name,
                "mobile": mobile,
                "location": location,
                "role": role,
                "first_login": True,
            },
        })
        auth_user = res.user
        if not auth_user:
            raise Exception("Auth user not created")
        user_id = auth_user.id
    except Exception as e:
        print("Supabase admin create_user error:", e)
        raise HTTPException(status_code=500, detail="Failed to create auth user")

    # 2) Optional: upload resume to Storage
    resume_url = None
    if role == "candidate" and resume is not None:
        try:
            file_bytes = await resume.read()
            path = f"{user_id}/{secrets.token_hex(4)}-{resume.filename}"
            storage_res = supabase.storage.from_("resumes").upload(path, file_bytes, {
                "contentType": resume.content_type or "application/octet-stream",
                "upsert": False,
            })
            # get public URL
            public_url_res = supabase.storage.from_("resumes").get_public_url(path)
            resume_url = public_url_res.get("data", {}).get("publicUrl")
        except Exception as e:
            print("Resume upload failed:", e)
            # Not fatal; continue

    # 3) Insert into public.users (or your custom table)
    try:
        insert_data = {
            "id": user_id,
            "full_name": full_name,
            "email": str(email),
            "mobile": mobile,
            "location": location,
            "role": role,
            "company_id": company_id if role == "recruiter" else None,
            "resume_url": resume_url if role == "candidate" else None,
        }
        db_res = supabase.table("users").insert(insert_data).execute()
        if db_res.error:
            raise Exception(db_res.error)
    except Exception as e:
        print("DB insert failed:", e)
        # attempt to clean up auth user
        try:
            supabase.auth.admin.delete_user(user_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to save user profile")

    # 4) Email the temp password via Resend
    email_sent = False
    try:
        html = f"""
        <div>
          <p>Hi {full_name},</p>
          <p>Welcome to Skreenit! Your account has been created successfully.</p>
          <p><strong>User ID:</strong> {email}<br/>
             <strong>Temporary Password:</strong> {temp_password}</p>
          <p>Please login and set a new password. After your first login, you'll be redirected to update your password.</p>
          <p>Login URL: <a href=\"{FRONTEND_BASE_URL}\">{FRONTEND_BASE_URL}</a></p>
          <p>Regards,<br/>Skreenit Team</p>
        </div>
        """
        email_sent = await send_resend_email(str(email), "Your Skreenit Account - Temporary Password", html)
    except Exception as e:
        print("Send email error:", e)

    return RegistrationResponse(
        user_id=user_id,
        email_sent=bool(email_sent),
        role=role,
        message="Registered successfully" if email_sent else "Registered successfully (email not sent)",
    )

@app.post("/auth/password-changed")
async def password_changed(payload: PasswordChangedRequest):
    html = f"""
    <div>
      <p>Hi {payload.full_name or payload.email},</p>
      <p>Your Skreenit account password was updated successfully.</p>
      <p>If you did not initiate this change, please contact support immediately.</p>
      <p>Regards,<br/>Skreenit Team</p>
    </div>
    """
    sent = await send_resend_email(str(payload.email), "Skreenit Password Updated", html)
    return {"email_sent": bool(sent)}

# Run: uvicorn backend.main:app --host 0.0.0.0 --port 8001
