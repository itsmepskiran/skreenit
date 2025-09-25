import os
import pytest
import requests

@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("SKREENIT_BASE_URL")
    if not url:
        pytest.skip("SKREENIT_BASE_URL not set; skipping API tests")
    return url.rstrip("/")

@pytest.fixture(scope="session")
def candidate_token() -> str | None:
    return os.getenv("CANDIDATE_TOKEN")

@pytest.fixture(scope="session")
def recruiter_token() -> str | None:
    return os.getenv("RECRUITER_TOKEN")

@pytest.fixture
def candidate_auth(candidate_token):
    headers = {}
    if candidate_token:
        headers["Authorization"] = f"Bearer {candidate_token}"
    return headers

@pytest.fixture
def recruiter_auth(recruiter_token):
    headers = {}
    if recruiter_token:
        headers["Authorization"] = f"Bearer {recruiter_token}"
    return headers
