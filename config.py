import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_PDF_EXTENSIONS = {".pdf"}
    ALLOWED_OFFICE_EXTENSIONS = {".docx", ".doc", ".pptx", ".xlsx"}

    TASK_POOL_WORKERS = int(os.environ.get("TASK_POOL_WORKERS", 2))
    TASK_TTL_SECONDS = 15 * 60

    DEFAULT_SENTENCES_PER_PAGE = 3
    SUMMARIZER_ALGORITHM = "lsa"

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")
    API_RATE_LIMIT = int(os.environ.get("API_RATE_LIMIT", 30))

    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
