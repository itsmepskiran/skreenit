import os
from typing import List, Union, Optional

class EmailError(Exception):
    """Custom exception for email sending errors."""
    pass

def send_email(
    to: Union[str, List[str]],
    subject: str,
    html: str,
    from_addr: Optional[str] = None
) -> dict:
    """
    Utility to send email via the Resend API.
    Raises EmailError on failure.
    """
    try:
        import resend
    except Exception as e:
        raise EmailError(f"Resend import failed: {e}")

    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise EmailError("Missing RESEND_API_KEY")

    resend.api_key = api_key

    if isinstance(to, str):
        to = [to]
    from_addr = from_addr or os.getenv("EMAIL_FROM", "info@skreenit.com")

    try:
        return resend.Emails.send({
            "from": from_addr,
            "to": to,
            "subject": subject,
            "html": html,
        })
    except Exception as e:
        raise EmailError(str(e))
