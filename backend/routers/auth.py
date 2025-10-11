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
    try:
        resume_bytes = await resume.read() if resume is not None else None
        result = auth_service.register(
            full_name=full_name,
            email=email,
            mobile=mobile,
            location=location,
            role=role,
            company_id=company_id,
            company_name=company_name,
            resume_bytes=resume_bytes,
            resume_filename=resume.filename if resume is not None else None
        )
        return {"ok": True, "data": result}
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

        # Mark password_set = True
        try:
            supabase.auth.admin.update_user_by_id(user.get("id"), {
                "user_metadata": {**(metadata or {}), "password_set": True}
            })
        except Exception:
            pass

        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
