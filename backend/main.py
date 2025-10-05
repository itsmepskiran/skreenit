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
        # Add your development subdomains here
        "http://auth.localhost:3000",
        "http://login.localhost:3000",
        "http://dashboards.localhost:3000",
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
                ".skreenit.com",
                ".onrender.com",
                ".railway.app"
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
