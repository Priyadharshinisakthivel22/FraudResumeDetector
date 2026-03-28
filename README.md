# Fraud Resume Detector

FastAPI service that implements an end-to-end fraud-aware resume verification workflow:

1. Resume upload and NLP extraction
2. OTP verification (email + phone)
3. GitHub/LinkedIn profile checks
4. Resume cross-checking and suspicious finding generation
5. Trust score calculation (0-100)
6. Candidate ranking (`>= 60`) vs limited trust
7. Interview questions or job suggestion email routing

## Run

```bash
pip install -e .
uvicorn app.main:app --reload
```

## Endpoints

- `POST /candidates/upload-resume`
- `POST /candidates/{id}/otp/send`
- `POST /candidates/{id}/otp/verify`
- `POST /candidates/{id}/profiles/verify`
- `POST /candidates/{id}/cross-check`
- `POST /candidates/{id}/score`
- `POST /candidates/{id}/finalize`
- `GET /health`
