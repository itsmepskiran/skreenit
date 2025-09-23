from fastapi import APIRouter, Request, HTTPException, Header, Form, UploadFile, File
from fastapi.responses import JSONResponse
import os, httpx, secrets, time
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@skreenit.app")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
router = APIRouter(tags=["auth"])
from models.auth_models import LoginRequest, PasswordChangedRequest

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"

def generate_temp_password(length: int = 12) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

@router.post("/login")
def login(payload: LoginRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"access_token": res.session.access_token, "user": res.user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
def validate_token(authorization: str = Header(..., convert_underscores=False)):
    token = authorization.replace("Bearer ", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    }
    try:
        res = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        res.raise_for_status()
        return {"user": res.json()}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/register")
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    location: str = Form(...),
    role: str = Form(...),
    company_id: str | None = Form(None),
    resume: UploadFile | None = File(None),
):
    try:
        temp_password = generate_temp_password(12)

        # Create user in Supabase Auth
        # Using sign_up to keep compatibility; optionally switch to admin.create_user to bypass email confirmation.
        auth_res = supabase.auth.sign_up({
            "email": email,
            "password": temp_password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "mobile": mobile,
                    "location": location,
                    "role": role,
                    "first_login": True,
                    **({"company_id": company_id} if company_id else {})
                }
            }
        })

        user = getattr(auth_res, "user", None)
        user_id = user.id if user else None
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user in Supabase")

        # Optional: upload resume to Supabase Storage
        resume_path = None
        if resume is not None:
            try:
                content = await resume.read()
                ts = int(time.time() * 1000)
                safe_name = resume.filename.replace(" ", "_")
                resume_path = f"{user_id}/{ts}-{safe_name}"
                up = supabase.storage.from_("resumes").upload(resume_path, content)
                if getattr(up, "error", None):
                    print("Resume upload error:", up.error)
            except Exception as ue:
                print("Resume upload failed:", ue)

        # Send email via Resend with temp password and links
        import resend
        resend.api_key = RESEND_API_KEY
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
            email_res = resend.Emails.send({
                "from": EMAIL_FROM,
                "to": [email],
                "subject": "Welcome to Skreenit - Your Account Details",
                "html": html,
            })
        except Exception as e:
            # Do not fail registration if email fails; just report status
            email_res = {"error": str(e)}

        return {
            "ok": True,
            "user_id": user_id,
            "resume_path": resume_path,
            "email": email,
            "email_sent": not isinstance(email_res, dict) or "error" not in email_res,
            "email_response": str(email_res),
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/password-changed")
async def password_changed(payload: PasswordChangedRequest):
    html = f"""
    <div>
      <p>Hi {payload.full_name or payload.email},</p>
      <p>Your Skreenit account password was updated successfully.</p>
      <p>If you did not initiate this change, please contact support immediately.</p>
      <p>Regards,<br/>Skreenit Team</p>
    </div>
    """
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        response = resend.Emails.send({
            "from": EMAIL_FROM,
            "to": [payload.email],
            "subject": "Skreenit Password Updated",
            "html": html
        })
        return {"email_sent": True, "response": response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
