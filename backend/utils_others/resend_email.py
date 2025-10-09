import os
from typing import List, Union, Optional

class EmailError(Exception):
    """Custom exception for email sending errors."""
    pass

def send_email(
    to: Union[str, List[str]],
    subject: str,
    html: str,
    from_addr: Optional[str] = None,
    email_type: str = "default"
) -> dict:
    """
    Utility to send email via the Resend API.
    Raises EmailError on failure.

    Args:
        email_type: Type of email ("welcome", "verification", "info", "support", "noreply")
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

    # Use different sender addresses based on email type
    if from_addr is None:
        email_senders = {
            "welcome": os.getenv("EMAIL_WELCOME", "welcome@skreenit.com"),
            "verification": os.getenv("EMAIL_VERIFICATION", "verification@skreenit.com"),
            "info": os.getenv("EMAIL_INFO", "info@skreenit.com"),
            "support": os.getenv("EMAIL_SUPPORT", "support@skreenit.com"),
            "noreply": os.getenv("EMAIL_NOREPLY", "do-not-reply@skreenit.com"),
            "default": os.getenv("EMAIL_FROM", "info@skreenit.com")
        }
        from_addr = email_senders.get(email_type, email_senders["default"])

    try:
        return resend.Emails.send({
            "from": from_addr,
            "to": to,
            "subject": subject,
            "html": html,
        })
    except Exception as e:
        raise EmailError(str(e))
