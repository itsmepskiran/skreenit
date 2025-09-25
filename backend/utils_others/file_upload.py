from typing import Optional
from supabase import Client

def upload_to_bucket(client: Client, bucket: str, path: str, content: bytes, content_type: Optional[str] = None) -> None:
    up = client.storage.from_(bucket).upload(path, content, {"contentType": content_type or "application/octet-stream"})
    if getattr(up, "error", None):
        raise Exception(up.error)


def create_signed_url(client: Client, bucket: str, path: str, expire_seconds: int = 3600) -> str:
    su = client.storage.from_(bucket).create_signed_url(path, expire_seconds)
    url = (su or {}).get("data", {}).get("signedUrl")
    if not url:
        raise Exception("failed to create signed url")
    return url
