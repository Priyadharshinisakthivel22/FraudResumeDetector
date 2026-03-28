from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProfileSnapshot, ResumeFact
from app.services.providers import GithubProvider, LinkedinProvider


class ProfileService:
    def __init__(self, github_provider: GithubProvider, linkedin_provider: LinkedinProvider) -> None:
        self.github_provider = github_provider
        self.linkedin_provider = linkedin_provider

    async def fetch_and_store(self, db: AsyncSession, candidate_id: int, resume_fact: ResumeFact) -> list[ProfileSnapshot]:
        snapshots: list[ProfileSnapshot] = []

        if resume_fact.github_url:
            gh_payload = await self.github_provider.fetch_profile(resume_fact.github_url)
            gh_snapshot = ProfileSnapshot(candidate_id=candidate_id, source="github", payload=gh_payload)
            db.add(gh_snapshot)
            snapshots.append(gh_snapshot)

        if resume_fact.linkedin_url:
            li_payload = await self.linkedin_provider.fetch_profile(resume_fact.linkedin_url)
            li_snapshot = ProfileSnapshot(candidate_id=candidate_id, source="linkedin", payload=li_payload)
            db.add(li_snapshot)
            snapshots.append(li_snapshot)

        await db.commit()
        return snapshots
