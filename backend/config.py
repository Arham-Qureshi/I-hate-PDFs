from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = ""
    API_SECRET_KEY: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB
    API_RATE_LIMIT: int = 30
    TASK_TTL_SECONDS: int = 900

    class Config:
        env_file = ".env"
