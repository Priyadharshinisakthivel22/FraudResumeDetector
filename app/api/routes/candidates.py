from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Candidate, ResumeFact, TrustState
from app.db.session import get_db
from app.schemas.candidate import CandidateCreated, OtpVerifyRequest, ScoreResponse
from app.services.audit import log_audit_event
from app.services.cross_check import CrossCheckService
from app.services.notifications import NotificationService
from app.services.otp_service import OtpService
from app.services.profile_service import ProfileService
from app.services.providers import EmailProvider, GithubProvider, LinkedinProvider, SmsProvider
from app.services.resume_parser import parse_resume_text
from app.services.scoring import ScoringService


router = APIRouter(prefix="/candidates", tags=["candidates"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload-resume", response_model=CandidateCreated)
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> CandidateCreated:
    data = await file.read()
    text = data.decode("utf-8", errors="ignore")
    parsed = parse_resume_text(text)

    save_path = UPLOAD_DIR / file.filename
    save_path.write_bytes(data)

    candidate = Candidate(
        full_name=parsed.full_name,
        email=parsed.email,
        phone=parsed.phone,
        resume_path=str(save_path),
        trust_state=TrustState.pending,
    )
    db.add(candidate)
    await db.flush()

    facts = ResumeFact(
        candidate_id=candidate.id,
        skills=parsed.skills,
        education=parsed.education,
        experience=parsed.experience,
        github_url=parsed.github_url,
        linkedin_url=parsed.linkedin_url,
    )
    db.add(facts)
    await db.commit()

    await log_audit_event(db, candidate.id, "resume_uploaded", {"filename": file.filename})
    return CandidateCreated(candidate_id=candidate.id)


@router.post("/{candidate_id}/otp/send")
async def send_otp(candidate_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    candidate = (await db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    otp_service = OtpService(EmailProvider(), SmsProvider())
    await otp_service.send_candidate_otps(db, candidate)
    await log_audit_event(db, candidate_id, "otp_sent", {})
    return {"status": "OTP sent"}


@router.post("/{candidate_id}/otp/verify")
async def verify_otp(candidate_id: int, payload: OtpVerifyRequest, db: AsyncSession = Depends(get_db)) -> dict:
    candidate = (await db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    otp_service = OtpService(EmailProvider(), SmsProvider())
    verified = await otp_service.verify_otps(db, candidate, payload.email_otp, payload.phone_otp)
    await log_audit_event(db, candidate_id, "otp_verified", {"verified": verified})
    return {"verified": verified, "trust_state": candidate.trust_state.value}


@router.post("/{candidate_id}/profiles/verify")
async def verify_profiles(candidate_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    candidate = (await db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one_or_none()
    facts = (await db.execute(select(ResumeFact).where(ResumeFact.candidate_id == candidate_id))).scalar_one_or_none()
    if not candidate or not facts:
        raise HTTPException(status_code=404, detail="Candidate not found")
    profile_service = ProfileService(GithubProvider(), LinkedinProvider())
    snapshots = await profile_service.fetch_and_store(db, candidate_id, facts)
    await log_audit_event(db, candidate_id, "profiles_verified", {"sources": [s.source for s in snapshots]})
    return {"snapshots": len(snapshots)}


@router.post("/{candidate_id}/cross-check")
async def cross_check(candidate_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    facts = (await db.execute(select(ResumeFact).where(ResumeFact.candidate_id == candidate_id))).scalar_one_or_none()
    if not facts:
        raise HTTPException(status_code=404, detail="Candidate facts not found")
    service = CrossCheckService()
    findings = await service.run(db, candidate_id, facts)
    await log_audit_event(db, candidate_id, "cross_checked", {"findings": len(findings)})
    return {"findings": len(findings)}


@router.post("/{candidate_id}/score", response_model=ScoreResponse)
async def score(candidate_id: int, db: AsyncSession = Depends(get_db)) -> ScoreResponse:
    candidate = (await db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    service = ScoringService()
    score_data = await service.score_candidate(db, candidate)
    await log_audit_event(db, candidate_id, "scored", {"final_score": score_data.final_score})
    return ScoreResponse(candidate_id=candidate_id, final_score=score_data.final_score, trust_state=candidate.trust_state.value)


@router.post("/{candidate_id}/finalize")
async def finalize(candidate_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    candidate = (await db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    service = NotificationService(EmailProvider())
    result = await service.dispatch_final_action(db, candidate)
    await log_audit_event(db, candidate_id, "finalized", {"result": result})
    return {"result": result}
