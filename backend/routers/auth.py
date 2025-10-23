from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import JSONResponse
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from models.auth_models import LoginRequest
from services.auth_service import AuthService
from typing import Optional

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

router = APIRouter(tags=["auth"])
auth_service = AuthService(supabase)

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
        result = auth_service.register(
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
        result = auth_service.login(request.email, request.password)
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
        user_info = auth_service.validate_token(token)
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
