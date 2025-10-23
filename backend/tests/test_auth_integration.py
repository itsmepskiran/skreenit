import os
import pytest
import requests
import asyncio
from typing import Dict, Any
from supabase import Client
from test_utils import (
    get_test_supabase_client,
    get_test_user_data,
    generate_test_password,
    TestUser,
    get_confirmation_email
)

@pytest.fixture
def supabase_client() -> Client:
    """Fixture for test Supabase client"""
    return get_test_supabase_client()

@pytest.fixture
def base_url() -> str:
    """Get base URL for API tests"""
    return os.getenv("SKREENIT_BASE_URL", "http://localhost:8000")

@pytest.mark.integration
class TestAuthenticationFlow:
    """
    Integration tests for the complete authentication flow:
    1. Registration
    2. Email confirmation
    3. Password setting
    4. Login
    5. Password reset
    """

    def test_registration_sends_confirmation(self, base_url, supabase_client):
        """Test that registration triggers confirmation email"""
        user_data = get_test_user_data()
        
        with TestUser(supabase_client, user_data) as test_user:
            # Register new user
            response = requests.post(
                f"{base_url}/auth/register",
                json=user_data,
                timeout=30
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["ok"] is True
            assert result["email_sent"] is True
            
            test_user.user_id = result["user_id"]
            
            # Verify user exists in Supabase but hasn't confirmed email
            user = supabase_client.auth.admin.get_user_by_id(test_user.user_id)
            assert user.user.email == user_data["email"]
            assert user.user.email_confirmed_at is None
            assert user.user.user_metadata["password_set"] is False

    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, base_url, supabase_client):
        """Test the complete registration flow including email confirmation"""
        user_data = get_test_user_data()
        new_password = generate_test_password()
        
        with TestUser(supabase_client, user_data) as test_user:
            # 1. Register user
            register_response = requests.post(
                f"{base_url}/auth/register",
                json=user_data,
                timeout=30
            )
            assert register_response.status_code == 200
            test_user.user_id = register_response.json()["user_id"]
            
            # 2. Get confirmation email
            confirmation_token = await get_confirmation_email(user_data["email"])
            assert confirmation_token, "Confirmation email not received"
            test_user.confirmation_token = confirmation_token
            
            # 3. Confirm email and set password
            confirm_response = requests.post(
                f"{base_url}/auth/confirm-email",
                json={
                    "token": confirmation_token,
                    "password": new_password
                },
                timeout=30
            )
            assert confirm_response.status_code == 200
            
            # 4. Try logging in with new password
            login_response = requests.post(
                f"{base_url}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": new_password
                },
                timeout=30
            )
            assert login_response.status_code == 200
            assert "access_token" in login_response.json()["data"]
            test_user.access_token = login_response.json()["data"]["access_token"]
            
            # 5. Verify user state
            user = supabase_client.auth.admin.get_user_by_id(test_user.user_id)
            assert user.user.email_confirmed_at is not None
            assert user.user.user_metadata["password_set"] is True

    @pytest.mark.asyncio
    async def test_password_reset_flow(self, base_url, supabase_client):
        """Test the password reset flow for an existing user"""
        # First create and confirm a user
        user_data = get_test_user_data()
        initial_password = generate_test_password()
        new_password = generate_test_password()
        
        with TestUser(supabase_client, user_data) as test_user:
            # Set up confirmed user (reusing previous test steps)
            await self.test_complete_registration_flow(base_url, supabase_client)
            
            # 1. Request password reset
            reset_request = requests.post(
                f"{base_url}/auth/forgot-password",
                json={"email": user_data["email"]},
                timeout=30
            )
            assert reset_request.status_code == 200
            
            # 2. Get reset email
            reset_token = await get_confirmation_email(user_data["email"])
            assert reset_token, "Password reset email not received"
            
            # 3. Reset password
            reset_response = requests.post(
                f"{base_url}/auth/reset-password",
                json={
                    "token": reset_token,
                    "password": new_password
                },
                timeout=30
            )
            assert reset_response.status_code == 200
            
            # 4. Try old password (should fail)
            old_login = requests.post(
                f"{base_url}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": initial_password
                },
                timeout=30
            )
            assert old_login.status_code in (400, 401)
            
            # 5. Login with new password
            new_login = requests.post(
                f"{base_url}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": new_password
                },
                timeout=30
            )
            assert new_login.status_code == 200
            assert "access_token" in new_login.json()["data"]