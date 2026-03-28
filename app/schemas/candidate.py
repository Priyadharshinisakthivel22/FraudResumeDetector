from pydantic import BaseModel


class CandidateCreated(BaseModel):
    candidate_id: int


class OtpVerifyRequest(BaseModel):
    email_otp: str
    phone_otp: str


class ScoreResponse(BaseModel):
    candidate_id: int
    final_score: float
    trust_state: str
