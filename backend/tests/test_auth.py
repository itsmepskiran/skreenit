import os
import pytest
import requests


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
