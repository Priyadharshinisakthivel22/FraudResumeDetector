import random
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Candidate, OtpChallenge, TrustState
from app.services.providers import EmailProvider, SmsProvider


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class OtpService:
    def __init__(self, email_provider: EmailProvider, sms_provider: SmsProvider) -> None:
        self.email_provider = email_provider
        self.sms_provider = sms_provider

    @staticmethod
    def _generate_otp() -> str:
        return str(random.randint(100000, 999999))

    async def send_candidate_otps(self, db: AsyncSession, candidate: Candidate) -> None:
        for channel, destination in (("email", candidate.email), ("phone", candidate.phone)):
            if not destination:
                continue
            otp = self._generate_otp()
            challenge = OtpChallenge(
                candidate_id=candidate.id,
                channel=channel,
                destination=destination,
                otp_hash=pwd_context.hash(otp),
                attempts=0,
                send_count=1,
                expires_at=datetime.utcnow() + timedelta(minutes=settings.otp_expiry_minutes),
            )
            db.add(challenge)
            if channel == "email":
                await self.email_provider.send_otp(destination, otp)
            else:
                await self.sms_provider.send_otp(destination, otp)
        await db.commit()

    async def verify_otps(self, db: AsyncSession, candidate: Candidate, email_otp: str, phone_otp: str) -> bool:
        challenges = (
            await db.execute(
                select(OtpChallenge).where(
                    OtpChallenge.candidate_id == candidate.id,
                    OtpChallenge.verified.is_(False),
                )
            )
        ).scalars().all()

        now = datetime.utcnow()
        verified_channels: set[str] = set()
        provided = {"email": email_otp, "phone": phone_otp}

        for challenge in challenges:
            if challenge.attempts >= settings.otp_max_attempts or challenge.expires_at < now:
                continue
            challenge.attempts += 1
            current_otp = provided.get(challenge.channel, "")
            if current_otp and pwd_context.verify(current_otp, challenge.otp_hash):
                challenge.verified = True
                verified_channels.add(challenge.channel)

        if "email" in verified_channels:
            candidate.otp_email_verified = True
        if "phone" in verified_channels:
            candidate.otp_phone_verified = True

        if not (candidate.otp_email_verified and candidate.otp_phone_verified):
            candidate.trust_state = TrustState.limited_trust

        await db.commit()
        return candidate.otp_email_verified and candidate.otp_phone_verified
