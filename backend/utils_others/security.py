from fastapi import HTTPException, Header
from typing import Optional

def get_user_from_bearer(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validates the provided token and returns a user context.
    Accepts either a full Authorization header value ("Bearer <token>") or a raw token string.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
     
    # Support both "Bearer <token>" and raw token
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
    # Example: decode/validate JWT or call Supabase user info API
    user = decode_your_token_or_call_supabase(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user

def ensure_role(user: dict, required_role: str) -> None:
    """
    Checks if a user has a required role and raises if not.
    """
    if user.get("role") != required_role:
        raise HTTPException(status_code=403, detail="Forbidden: insufficient role.")

# Stub for real decoding or validation
def decode_your_token_or_call_supabase(token: str) -> Optional[dict]:
    # Implement your real validation here
    # For now, just stub out to allow integration
    return {"id": "user_id", "role": "candidate"}  # Example structure
