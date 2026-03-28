import random


class EmailProvider:
    async def send_otp(self, destination: str, otp: str) -> None:
        print(f"Email OTP sent to {destination}: {otp}")

    async def send_interview_questions(self, destination: str, questions: list[str]) -> None:
        print(f"Interview questions sent to {destination}: {questions}")

    async def send_job_recommendations(self, destination: str, recommendations: list[str]) -> None:
        print(f"Job recommendations sent to {destination}: {recommendations}")


class SmsProvider:
    async def send_otp(self, destination: str, otp: str) -> None:
        print(f"SMS OTP sent to {destination}: {otp}")


class GithubProvider:
    async def fetch_profile(self, profile_url: str) -> dict:
        # Placeholder adapter - replace with actual GitHub API calls.
        return {
            "profile_url": profile_url,
            "languages": ["python", "sql", "docker"],
            "projects": 8,
            "contributions_last_year": 230,
            "experience_years": 3,
        }


class LinkedinProvider:
    async def fetch_profile(self, profile_url: str) -> dict:
        # Placeholder adapter - replace with actual LinkedIn integration.
        return {
            "profile_url": profile_url,
            "skills": ["python", "fastapi", "aws"],
            "education": ["Bachelor of Technology"],
            "experience_years": random.randint(2, 6),
        }
