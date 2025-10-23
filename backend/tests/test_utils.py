import os
import secrets
import string
import pytest
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load test environment variables
load_dotenv("tests/test.env")

def get_test_supabase_client() -> Client:
    """Get Supabase client configured for testing"""
    url = os.getenv("SUPABASE_TEST_URL")
    key = os.getenv("SUPABASE_TEST_SERVICE_ROLE_KEY")
    if not url or not key:
        pytest.skip("Supabase test credentials not configured")
    return create_client(url, key)

def generate_test_email() -> str:
    """Generate a unique test email address"""
    random_id = secrets.token_hex(6)
    domain = os.getenv("TEST_EMAIL_DOMAIN", "@skreenit-test.com")
    return f"test_{random_id}{domain}"

def generate_test_password(length: int = 12) -> str:
    """Generate a secure password for testing"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_test_user_data(
    email: Optional[str] = None,
    role: str = "candidate"
) -> Dict[str, Any]:
    """Generate test user data"""
    return {
        "email": email or generate_test_email(),
        "full_name": "Test User",
        "mobile": "1234567890",
        "location": "Test Location",
        "role": role
    }

def cleanup_test_user(client: Client, user_id: str) -> None:
    """Clean up test user data after tests"""
    try:
        client.auth.admin.delete_user(user_id)
    except Exception:
        pass  # Ignore cleanup errors

class TestUser:
    """Test user context manager for automatic cleanup"""
    def __init__(self, client: Client, user_data: Dict[str, Any]):
        self.client = client
        self.user_data = user_data
        self.user_id = None
        self.confirmation_token = None
        self.access_token = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.user_id:
            cleanup_test_user(self.client, self.user_id)

async def get_confirmation_email(user_email: str, timeout: int = 30) -> Optional[str]:
    """
    Get confirmation email from test email service.
    You'll need to implement this based on your email testing strategy.
    Options:
    1. Use a test email service API
    2. Use a mock SMTP server
    3. Use Supabase's test email templates
    """
    # This is a placeholder - implement based on your email testing strategy
    return None