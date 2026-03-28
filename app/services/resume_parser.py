import re
from dataclasses import dataclass


@dataclass
class ParsedResume:
    full_name: str
    email: str
    phone: str
    skills: list[str]
    education: list[str]
    experience: list[str]
    github_url: str
    linkedin_url: str


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\+?\d[\d -]{7,}\d")
GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+")

KNOWN_SKILLS = {
    "python",
    "java",
    "sql",
    "fastapi",
    "django",
    "javascript",
    "react",
    "docker",
    "kubernetes",
    "aws",
}


def parse_resume_text(text: str) -> ParsedResume:
    email = EMAIL_RE.search(text).group(0) if EMAIL_RE.search(text) else ""
    phone = PHONE_RE.search(text).group(0) if PHONE_RE.search(text) else ""
    github = GITHUB_RE.search(text).group(0) if GITHUB_RE.search(text) else ""
    linkedin = LINKEDIN_RE.search(text).group(0) if LINKEDIN_RE.search(text) else ""

    lower_text = text.lower()
    skills = sorted([s for s in KNOWN_SKILLS if s in lower_text])
    education = [line.strip() for line in text.splitlines() if "university" in line.lower() or "bachelor" in line.lower()]
    experience = [line.strip() for line in text.splitlines() if "years" in line.lower() or "experience" in line.lower()]
    name = next((line.strip() for line in text.splitlines() if line.strip()), "Unknown Candidate")

    return ParsedResume(
        full_name=name,
        email=email,
        phone=phone,
        skills=skills,
        education=education[:5],
        experience=experience[:10],
        github_url=github,
        linkedin_url=linkedin,
    )
