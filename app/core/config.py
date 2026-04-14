from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "General Purpose Bias Auditor"
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    HF_TOKEN: str
    class Config:
        env_file = ".env"

settings = Settings()