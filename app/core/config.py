from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fraud Resume Detector"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fraud_resume"
    otp_expiry_minutes: int = 10
    otp_max_attempts: int = 5
    otp_send_limit_per_hour: int = 5
    score_threshold: float = 60.0
    email_from: str = "noreply@example.com"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FRD_")


settings = Settings()
