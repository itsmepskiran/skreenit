import os
import httpx
from typing import Optional, Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class AuthUser(dict):
    @property
    def id(self) -> Optional[str]:
        return self.get("id")
    @property
    def role(self) -> Optional[str]:
        return (self.get("user_metadata") or {}).get("role")


def get_user_from_bearer(bearer_token: str) -> AuthUser:
    if not bearer_token:
        raise ValueError("Missing bearer token")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY or "",
    }
    resp = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
    resp.raise_for_status()
    return AuthUser(resp.json())


def ensure_role(user: AuthUser, expected_role: str) -> None:
    if not user or user.role != expected_role:
        raise PermissionError("Forbidden: wrong role")
