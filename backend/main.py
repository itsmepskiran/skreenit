import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auth,
    applicant,
    recruiter,
    dashboard,
    video,
    notification,
    analytics
)
from utils_others.error_handler import register_exception_handlers
from supabase import create_client, Client

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Application setup
app = FastAPI(
    title="Skreenit Application",
    description="Skreenit Testing platform, HR automation, and candidate screening.",
    version="1.0.0"
)

# Enable CORS for frontend
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")
origins = [x.strip() for x in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handling
register_exception_handlers(app)

# App routers
app.include_router(auth.router, prefix="/auth")
app.include_router(applicant.router, prefix="/applicant")
app.include_router(recruiter.router, prefix="/recruiter")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(video.router, prefix="/video")
app.include_router(notification.router, prefix="/notification")
app.include_router(analytics.router, prefix="/analytics")

# Root
@app.get("/")
def read_root():
    return {"message": "Welcome to the HR/Candidate Screening Platform API!"}

# Health check endpoint for local/staging probes and Postman tests
@app.get("/health")
def health_check():
    return {"status": "ok"}
