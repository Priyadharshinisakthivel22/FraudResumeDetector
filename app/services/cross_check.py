from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProfileSnapshot, ResumeFact, VerificationFinding


class CrossCheckService:
    async def run(self, db: AsyncSession, candidate_id: int, resume_fact: ResumeFact) -> list[VerificationFinding]:
        snapshots = (
            await db.execute(select(ProfileSnapshot).where(ProfileSnapshot.candidate_id == candidate_id))
        ).scalars().all()
        findings: list[VerificationFinding] = []

        resume_skills = set(map(str.lower, resume_fact.skills or []))
        resume_exp_lines = resume_fact.experience or []
        declared_experience_years = self._extract_declared_experience_years(resume_exp_lines)

        profile_skills: set[str] = set()
        profile_experience_years: list[int] = []
        profile_education: list[str] = []
        for snap in snapshots:
            payload = snap.payload or {}
            profile_skills.update(map(str.lower, payload.get("skills", [])))
            profile_skills.update(map(str.lower, payload.get("languages", [])))
            if payload.get("experience_years") is not None:
                profile_experience_years.append(int(payload["experience_years"]))
            profile_education.extend(payload.get("education", []))

        missing_skills = sorted(list(resume_skills - profile_skills))
        if missing_skills:
            findings.append(
                VerificationFinding(
                    candidate_id=candidate_id,
                    category="skills",
                    severity="medium",
                    detail=f"Skills not verified via profiles: {', '.join(missing_skills)}",
                )
            )

        if declared_experience_years > 0 and profile_experience_years:
            avg_profile_exp = sum(profile_experience_years) / len(profile_experience_years)
            if declared_experience_years - avg_profile_exp >= 2:
                findings.append(
                    VerificationFinding(
                        candidate_id=candidate_id,
                        category="experience",
                        severity="high",
                        detail=f"Declared experience ({declared_experience_years}y) exceeds profile average ({avg_profile_exp:.1f}y).",
                    )
                )

        if resume_fact.education and not profile_education:
            findings.append(
                VerificationFinding(
                    candidate_id=candidate_id,
                    category="education",
                    severity="low",
                    detail="Resume education could not be verified from profiles.",
                )
            )

        for finding in findings:
            db.add(finding)
        await db.commit()
        return findings

    @staticmethod
    def _extract_declared_experience_years(lines: list[str]) -> int:
        for line in lines:
            tokens = line.lower().replace("+", "").split()
            for idx, token in enumerate(tokens):
                if token.isdigit() and idx + 1 < len(tokens) and tokens[idx + 1].startswith("year"):
                    return int(token)
        return 0
