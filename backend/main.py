# FastAPI backend for Skreenit multi-subdomain platform
# Supports: auth, login, applicant, recruiter, dashboard flows

import os, secrets, httpx
from pathlib import Path
from typing import Optional
from routers import auth, applicant, recruiter, dashboard, video, notification, analytics

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

# ---------- Environment Setup ----------
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://login.skreenit.com")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", FRONTEND_BASE_URL).split(",")

print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_SERVICE_ROLE_KEY:", SUPABASE_SERVICE_ROLE_KEY)
print("✅ Running main.py from:", __file__)

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ---------- App Setup ----------
app = FastAPI(title="Skreenit Backend", version="2.0.0")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(applicant.router, prefix="/applicant", tags=["applicant"])
app.include_router(recruiter.router, prefix="/recruiter", tags=["recruiter"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(video.router, prefix="/video", tags=["video"])
app.include_router(notification.router, prefix="/notification", tags=["notification"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class HealthResponse(BaseModel):
    status: str

# ---------- Utils ----------
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"

def generate_temp_password(length: int = 12) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

# ---------- Routes ----------

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")

# ---------- Optional: Global Error Handler ----------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print("Unhandled error:", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
