from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from models.auth_models import LoginRequest
from services.auth_service import AuthService
from services.supabase_client import get_client
from typing import Optional

# Do NOT create the Supabase client at module import time. Creating it during import
# will cause the app to crash on startup when environment secrets are not yet provided
# by the hosting environment. Instead we lazily initialize the client and AuthService
# on first request. This keeps the app importable and avoids deployment failures.
load_dotenv()

router = APIRouter(tags=["auth"])
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        # Attempt to create a Supabase client from environment
        try:
            supabase = get_client()
        except Exception as e:
            # Re-raise a clear error so endpoints can return a controlled response
            raise RuntimeError("Supabase client not configured: " + str(e)) from e
        _auth_service = AuthService(supabase)
    return _auth_service

@router.post("/register")
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    location: str = Form(...),
    role: str = Form(...),
    company_id: str = Form(None),
    company_name: str = Form(None),
    resume: UploadFile = File(None)
):
    """Register a new user with role-specific handling"""
    try:
        # Validate role
        if role not in ['candidate', 'recruiter']:
            raise HTTPException(status_code=400, detail="Invalid role specified")
        
        # Validate recruiter-specific fields
        if role == 'recruiter' and not company_name:
            raise HTTPException(status_code=400, detail="Company name is required for recruiter registration")
            
        # Handle resume for candidates
        resume_bytes = None
        resume_filename = None
        if resume and role == 'candidate':
            # Validate file type
            allowed_types = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if resume.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid resume format. Please upload PDF or DOC/DOCX file")
            resume_bytes = await resume.read()
            resume_filename = resume.filename
            
        # Register user
        try:
            service = get_auth_service()
        except RuntimeError as re:
            return JSONResponse(status_code=500, content={"ok": False, "error": str(re)})

        result = service.register(
            full_name=full_name,
            email=email,
            mobile=mobile,
            location=location,
            role=role,
            company_id=company_id,
            company_name=company_name,
            resume_bytes=resume_bytes,
            resume_filename=resume_filename
        )
        
        return {
            "ok": True,
            "data": result,
            "message": "Registration successful! Please check your email to verify your account."
        }
    except HTTPException as he:
        return JSONResponse(status_code=he.status_code, content={"ok": False, "error": he.detail})
    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})

@router.post("/login")
async def login(request: LoginRequest):
    try:
        try:
            service = get_auth_service()
        except RuntimeError as re:
            return JSONResponse(status_code=500, content={"ok": False, "error": str(re)})

        result = service.login(request.email, request.password)
        return result  # already {"ok": True, "data": {...}}
    except Exception as e:
        return JSONResponse(status_code=401, content={"ok": False, "error": str(e)})

@router.post("/password-updated")
async def password_updated(request: Request):
    try:
        auth_header: Optional[str] = request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"ok": False, "error": "Missing Authorization header"})
        token = auth_header.split(" ", 1)[1]
        try:
            service = get_auth_service()
        except RuntimeError as re:
            return JSONResponse(status_code=500, content={"ok": False, "error": str(re)})

        user_info = service.validate_token(token)
        user = user_info.get("user") or {}
        email = user.get("email")
        metadata = user.get("user_metadata") or {}
        role = metadata.get("role")
        full_name = metadata.get("full_name") or None

        try:
            _ = auth_service.notify_password_changed(email=email, full_name=full_name)
        except Exception:
            pass

        if role == "recruiter":
            try:
                company = auth_service.get_recruiter_company_info(user.get("id"))
                cid = company.get("company_id")
                cname = company.get("company_name")
                if cid:
                    _ = auth_service.send_recruiter_company_email(email=email, full_name=full_name, company_id=cid, company_name=cname)
            except Exception:
                pass

        # After updating metadata, return user info for frontend to handle login
        return {"ok": True, "data": {"user": user, "message": "Password updated successfully. Please log in."}}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
