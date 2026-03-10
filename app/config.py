from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "adaptiq"

    # AI provider: "groq", "gemini", or "anthropic"
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    MAX_QUESTIONS_PER_SESSION: int = 20
    AI_INSIGHT_TRIGGER: int = 10
    ABILITY_INITIAL: float = 0.5
    ABILITY_MIN: float = 0.1
    ABILITY_MAX: float = 1.0

    class Config:
        env_file = ".env"


settings = Settings()
