import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import auth, applicant, recruiter, dashboard, analytics, notification, video

# Initialize FastAPI app
app = FastAPI(
    title="Skreenit API",
    description="Backend API for Skreenit recruitment platform",
    version="1.0.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Skreenit API is running"}

# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(applicant.router, prefix="/applicant")
app.include_router(recruiter.router, prefix="/recruiter")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(analytics.router, prefix="/analytics")
app.include_router(notification.router, prefix="/notification")
app.include_router(video.router, prefix="/video")

# Enable CORS for frontend
# Environment-based CORS configuration for security
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")

if ALLOWED_ORIGINS:
    # Production: Use explicit allowed origins from environment
    origins = [x.strip() for x in ALLOWED_ORIGINS.split(",")]
else:
    # Development: Allow common development URLs
    origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        # Production skreenit.com subdomains
        "https://www.skreenit.com",
        "https://skreenit.com",
        "https://login.skreenit.com",
        "https://auth.skreenit.com",
        "https://applicant.skreenit.com",
        "https://recruiter.skreenit.com",
        "https://dashboard.skreenit.com",
        # Development subdomains
        "http://auth.localhost:3000",
        "http://login.localhost:3000",
        "http://dashboard.localhost:3000",
        "http://applicant.localhost:3000",
        "http://recruiter.localhost:3000"
    ]

# Validate origins to prevent security issues
def validate_origins(origins_list):
    """Validate and filter origins for security"""
    validated_origins = []
    for origin in origins_list:
        origin = origin.strip()
        if not origin:
            continue

        # Basic validation - only allow http/https protocols
        if not origin.startswith(('http://', 'https://')):
            print(f"Warning: Invalid origin format: {origin}")
            continue

        # In production, be more restrictive
        if os.getenv("ENVIRONMENT") == "production":
            # Only allow specific production domains
            allowed_domains = [
                ".skreenit.com"
            ]
            if not any(domain in origin for domain in allowed_domains):
                print(f"Warning: Production origin not in allowed domains: {origin}")
                continue

        validated_origins.append(origin)

    return validated_origins

# Apply validation
origins = validate_origins(origins)

# Ensure we have at least one origin
if not origins:
    # Fallback to localhost for development
    origins = ["http://localhost:3000"]
    print("Warning: No valid origins configured, using localhost fallback")

print(f"CORS enabled for origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since"
    ],
)
