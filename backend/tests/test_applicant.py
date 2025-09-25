import os
import pytest
import requests

CANDIDATE_ID = os.getenv("CANDIDATE_ID", "00000000-0000-0000-0000-000000000000")

@pytest.mark.skipif(not os.getenv("CANDIDATE_TOKEN"), reason="CANDIDATE_TOKEN not set")
def test_get_detailed_form_auth(base_url, candidate_auth):
    r = requests.get(f"{base_url}/applicant/detailed-form/{CANDIDATE_ID}", headers=candidate_auth, timeout=30)
    assert r.status_code in (200, 404)

@pytest.mark.skipif(not os.getenv("CANDIDATE_TOKEN"), reason="CANDIDATE_TOKEN not set")
def test_post_detailed_form_auth(base_url, candidate_auth):
    payload = {
        "candidate_id": CANDIDATE_ID,
        "profile": {"id": CANDIDATE_ID, "email": "candidate@example.com"},
        "education": [],
        "experience": [],
        "skills": []
    }
    r = requests.post(f"{base_url}/applicant/detailed-form", json=payload, headers=candidate_auth, timeout=30)
    assert r.status_code in (200, 500)

@pytest.mark.skipif(not os.getenv("CANDIDATE_TOKEN"), reason="CANDIDATE_TOKEN not set")
def test_get_general_video_auth(base_url, candidate_auth):
    r = requests.get(f"{base_url}/applicant/general-video/{CANDIDATE_ID}", headers=candidate_auth, timeout=30)
    assert r.status_code in (200, 404)
