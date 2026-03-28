import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrustState(str, enum.Enum):
    pending = "pending"
    ranked = "ranked"
    limited_trust = "limited_trust"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    resume_path: Mapped[str] = mapped_column(String(500), default="")
    otp_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    otp_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_state: Mapped[TrustState] = mapped_column(Enum(TrustState), default=TrustState.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume_facts = relationship("ResumeFact", back_populates="candidate", uselist=False)
    findings = relationship("VerificationFinding", back_populates="candidate")
    scores = relationship("TrustScore", back_populates="candidate")


class ResumeFact(Base):
    __tablename__ = "resume_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), unique=True)
    skills: Mapped[dict] = mapped_column(JSON, default=list)
    education: Mapped[dict] = mapped_column(JSON, default=list)
    experience: Mapped[dict] = mapped_column(JSON, default=list)
    github_url: Mapped[str] = mapped_column(String(500), default="")
    linkedin_url: Mapped[str] = mapped_column(String(500), default="")

    candidate = relationship("Candidate", back_populates="resume_facts")


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    channel: Mapped[str] = mapped_column(String(20))
    destination: Mapped[str] = mapped_column(String(255))
    otp_hash: Mapped[str] = mapped_column(String(255))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    send_count: Mapped[int] = mapped_column(Integer, default=1)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProfileSnapshot(Base):
    __tablename__ = "profile_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    source: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VerificationFinding(Base):
    __tablename__ = "verification_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    category: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="findings")


class TrustScore(Base):
    __tablename__ = "trust_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    otp_score: Mapped[float] = mapped_column(Float)
    profile_score: Mapped[float] = mapped_column(Float)
    skill_score: Mapped[float] = mapped_column(Float)
    experience_score: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float] = mapped_column(Float)
    rationale: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="scores")


class CandidateOutcome(Base):
    __tablename__ = "candidate_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), unique=True)
    result: Mapped[str] = mapped_column(String(30))
    action_dispatched: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    event_type: Mapped[str] = mapped_column(String(80))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
