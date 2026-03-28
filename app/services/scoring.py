from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Candidate, CandidateOutcome, ProfileSnapshot, TrustScore, TrustState, VerificationFinding


class ScoringService:
    OTP_WEIGHT = 35.0
    PROFILE_WEIGHT = 25.0
    SKILL_WEIGHT = 20.0
    EXP_WEIGHT = 20.0

    async def score_candidate(self, db: AsyncSession, candidate: Candidate) -> TrustScore:
        findings = (
            await db.execute(select(VerificationFinding).where(VerificationFinding.candidate_id == candidate.id))
        ).scalars().all()
        snapshots = (
            await db.execute(select(ProfileSnapshot).where(ProfileSnapshot.candidate_id == candidate.id))
        ).scalars().all()

        otp_score = 100.0 if (candidate.otp_email_verified and candidate.otp_phone_verified) else 30.0
        profile_score = 100.0 if len(snapshots) >= 2 else 55.0 if len(snapshots) == 1 else 20.0

        skill_penalty = sum(15 for f in findings if f.category == "skills")
        exp_penalty = sum(25 for f in findings if f.category == "experience" and f.severity == "high")
        edu_penalty = sum(10 for f in findings if f.category == "education")

        skill_score = max(0.0, 100.0 - skill_penalty)
        experience_score = max(0.0, 100.0 - exp_penalty - edu_penalty)

        final_score = (
            (otp_score * self.OTP_WEIGHT)
            + (profile_score * self.PROFILE_WEIGHT)
            + (skill_score * self.SKILL_WEIGHT)
            + (experience_score * self.EXP_WEIGHT)
        ) / 100.0

        if not (candidate.otp_email_verified and candidate.otp_phone_verified):
            final_score = min(final_score, 59.0)

        score = TrustScore(
            candidate_id=candidate.id,
            otp_score=otp_score,
            profile_score=profile_score,
            skill_score=skill_score,
            experience_score=experience_score,
            final_score=round(final_score, 2),
            rationale={
                "weights": {
                    "otp": self.OTP_WEIGHT,
                    "profile": self.PROFILE_WEIGHT,
                    "skill": self.SKILL_WEIGHT,
                    "experience": self.EXP_WEIGHT,
                },
                "finding_count": len(findings),
            },
        )
        db.add(score)

        outcome_result = "ranked" if score.final_score >= settings.score_threshold else "limited_trust"
        candidate.trust_state = TrustState.ranked if outcome_result == "ranked" else TrustState.limited_trust

        existing_outcome = (
            await db.execute(select(CandidateOutcome).where(CandidateOutcome.candidate_id == candidate.id))
        ).scalar_one_or_none()
        if existing_outcome:
            existing_outcome.result = outcome_result
        else:
            db.add(CandidateOutcome(candidate_id=candidate.id, result=outcome_result, action_dispatched=False))

        await db.commit()
        return score
