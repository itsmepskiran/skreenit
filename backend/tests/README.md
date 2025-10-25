# Skreenit Backend Tests (pytest)

These tests are designed to run against a deployed or locally running FastAPI backend.

## Prerequisites

- Python 3.10+
- `pytest` and `requests` installed:
  
  ```bash
  pip install -U pytest requests
  ```

## Configuration via environment variables

The tests use environment variables for base URL and bearer tokens.

- `SKREENIT_BASE_URL` (required): e.g. `https://auth.skreenit.com` or `http://127.0.0.1:8000`
- `CANDIDATE_TOKEN` (optional, required for candidate-protected tests)
- `RECRUITER_TOKEN` (optional, required for recruiter-protected tests)
- `CANDIDATE_ID` (optional; used by some tests)
- `RECRUITER_ID` (optional; used by some tests)
- `JOB_ID`, `APPLICATION_ID` (optional; used by recruiter tests if provided)

Example (PowerShell):

```powershell
$env:SKREENIT_BASE_URL = "https://auth.skreenit.com"
$env:CANDIDATE_TOKEN = "eyJ..."
$env:RECRUITER_TOKEN = "eyJ..."
$env:CANDIDATE_ID = "00000000-0000-0000-0000-000000000000"
$env:RECRUITER_ID = "00000000-0000-0000-0000-000000000000"
pytest -q
```

## Notes

- Tests gracefully skip sections if required env vars are not present.
- These tests do not create or modify real data unless you point them at a writeable environment. Use a staging env.
