from typing import Optional
from supabase import Client

def upload_to_bucket(
    client: Client,
    bucket: str,
    path: str,
    content: bytes,
    content_type: Optional[str] = None
) -> None:
    """
    Uploads content to a specified Supabase Storage bucket.
    """
    up = client.storage.from_(bucket).upload(path, content, content_type or "application/octet-stream")
    if getattr(up, "error", None):
        raise Exception(f"Upload error: {up.error}")

def create_signed_url(
    client: Client,
    bucket: str,
    path: str,
    expire_seconds: int = 3600
) -> str:
    """
    Generates a signed URL for accessing content in a Supabase bucket.
    """
    su = client.storage.from_(bucket).create_signed_url(path, expire_seconds)
    url = getattr(su, "data", {}).get("signedUrl") if hasattr(su, "data") else None
    if not url:
        raise Exception("Failed to create signed URL")
    return url
