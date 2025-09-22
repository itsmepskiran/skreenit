from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import os, httpx
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
