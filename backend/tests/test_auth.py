import os
import pytest
import requests
import secrets
import string


def test_health(base_url):
    r = requests.get(f"{base_url}/health", timeout=30)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_validate_requires_token(base_url):
    r = requests.post(f"{base_url}/auth/validate", timeout=30)
    assert r.status_code in (400, 401)


@pytest.mark.skipif(not os.getenv("CANDIDATE_TOKEN"), reason="CANDIDATE_TOKEN not set")
def test_validate_with_candidate_token(base_url):
    token = os.getenv("CANDIDATE_TOKEN")
    r = requests.post(
        f"{base_url}/auth/validate",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert r.status_code == 200
    assert "user" in r.json()


def generate_test_password(length=12):
    """Generate a secure test password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@pytest.fixture
def test_user_credentials():
    """Fixture to create test user credentials"""
    return {
        "email": f"test_{secrets.token_hex(4)}@skreenit-test.com",
        "password": generate_test_password(),
        "full_name": "Test User",
        "mobile": "1234567890",
        "location": "Test Location",
        "role": "candidate"
    }


def test_user_registration_flow(base_url, test_user_credentials):
    """Test the complete user registration flow"""
    # Register new user - should NOT include password
    register_data = {
        "email": test_user_credentials["email"],
        "full_name": test_user_credentials["full_name"],
        "mobile": test_user_credentials["mobile"],
        "location": test_user_credentials["location"],
        "role": test_user_credentials["role"]
    }
    
    register_response = requests.post(
        f"{base_url}/auth/register",
        json=register_data,
        timeout=30
    )
    assert register_response.status_code == 200
    assert register_response.json().get("ok") is True
    assert register_response.json().get("email_sent") is True
    
    # At this point in a real scenario:
    # 1. User would receive confirmation email
    # 2. Click the confirmation link
    # 3. Be redirected to update-password page
    # 4. Set their password
    
    # Note: Can't test login before email confirmation and password set
    unconfirmed_login = requests.post(
        f"{base_url}/auth/login",
        json={
            "email": test_user_credentials["email"],
            "password": "any_password"
        },
        timeout=30
    )
    # Should fail because email isn't confirmed and password isn't set
    assert unconfirmed_login.status_code in (400, 401)


@pytest.mark.skip(reason="Requires Supabase email confirmation flow")
def test_password_set_after_confirmation(base_url, test_user_credentials):
    """
    Test setting password after email confirmation.
    Note: This test is skipped because it requires email confirmation flow.
    In a real scenario:
    1. User registers (done in test_user_registration_flow)
    2. Gets confirmation email from Supabase
    3. Clicks confirmation link
    4. Gets redirected to password update page
    5. Sets their initial password
    6. Can then login with that password
    """
    # This would be the flow after email confirmation
    new_password = generate_test_password()
    
    # In reality, this requires the email confirmation token from Supabase
    # which we can't get in an automated test
    update_response = requests.post(
        f"{base_url}/auth/update-password",
        json={
            "email": test_user_credentials["email"],
            "new_password": new_password,
            "confirmation_token": "would_come_from_email"
        },
        timeout=30
    )
    
    # Since we can't test the actual flow without email confirmation,
    # we'll skip the assertions
    pytest.skip("Requires email confirmation flow")
