from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "General Purpose Bias Auditor"
    GROQ_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None
    class Config:
        env_file = ".env"

settings = Settings()