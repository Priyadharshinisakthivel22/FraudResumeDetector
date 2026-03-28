from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Candidate, CandidateOutcome
from app.services.providers import EmailProvider


class NotificationService:
    def __init__(self, email_provider: EmailProvider) -> None:
        self.email_provider = email_provider

    async def dispatch_final_action(self, db: AsyncSession, candidate: Candidate) -> str:
        outcome = (
            await db.execute(select(CandidateOutcome).where(CandidateOutcome.candidate_id == candidate.id))
        ).scalar_one_or_none()
        if not outcome:
            return "Outcome not found"
        if outcome.action_dispatched:
            return "Already dispatched"

        if outcome.result == "ranked":
            await self.email_provider.send_interview_questions(
                candidate.email,
                [
                    "Explain a challenging project where you solved performance bottlenecks.",
                    "How do you verify correctness in production-critical code?",
                ],
            )
        else:
            await self.email_provider.send_job_recommendations(
                candidate.email,
                [
                    "Backend Engineer (Python/FastAPI)",
                    "Data Analyst (SQL/Python)",
                ],
            )

        outcome.action_dispatched = True
        await db.commit()
        return outcome.result
