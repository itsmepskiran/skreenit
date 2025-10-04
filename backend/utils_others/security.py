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
