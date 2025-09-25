from fastapi import APIRouter, Request, HTTPException, Header, Form, UploadFile, File
from fastapi.responses import JSONResponse
import os, httpx
from supabase import create_client, Client
from dotenv import load_dotenv
from models.auth_models import LoginRequest, PasswordChangedRequest
from services.auth_service import AuthService

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
router = APIRouter(tags=["auth"])
auth_service = AuthService(supabase)

@router.post("/login")
def login(payload: LoginRequest):
    try:
        return auth_service.login(payload.email, payload.password)
    except Exception as e:
        msg = str(e)
        # Normalize common Supabase auth error into 401 for the client
        if "Invalid login credentials" in msg or "invalid login credentials" in msg:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        raise HTTPException(status_code=500, detail=msg)

@router.post("/validate")
def validate_token(authorization: str = Header(..., convert_underscores=False)):
    try:
        token = authorization.replace("Bearer ", "")
        return auth_service.validate_token(token)
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
        resume_bytes = await resume.read() if resume is not None else None
        result = auth_service.register(
            full_name=full_name,
            email=email,
            mobile=mobile,
            location=location,
            role=role,
            company_id=company_id,
            resume_bytes=resume_bytes,
            resume_filename=resume.filename if resume is not None else None,
        )
        return result
    except ValueError as ve:
        # For duplicate user case
        if str(ve) == "User already registered":
            raise HTTPException(status_code=409, detail="User already registered")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/password-changed")
async def password_changed(payload: PasswordChangedRequest):
    try:
        # Prefer provided full_name; otherwise service will fallback
        return auth_service.notify_password_changed(email=payload.email, full_name=payload.full_name)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
