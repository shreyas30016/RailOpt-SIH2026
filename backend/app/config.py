import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_default_database_url() -> str:
    db_url = os.getenv("DATABASE_URL", "")
    is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))
    if is_serverless:
        if not db_url or db_url.startswith("sqlite"):
            return "sqlite:////tmp/railopt.db"
        return db_url
    if db_url:
        return db_url
    return f"sqlite:///{BASE_DIR}/railopt.db"

class Settings(BaseModel):
    PROJECT_NAME: str = "Indian Railways Block Planning & Optimization (RailOpt)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = get_default_database_url()
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SOLVER_TIMEOUT_SECONDS: int = int(os.getenv("SOLVER_TIMEOUT_SECONDS", "15"))
    DEFAULT_CORRIDOR: str = "Delhi-Agra Mainline (Northern Railway)"

    # Live / Public Train Data Settings
    TRAIN_DATA_PROVIDER: str = os.getenv("TRAIN_DATA_PROVIDER", "auto") # auto, live, mock
    LIVE_TRAIN_API_URL: str = os.getenv("LIVE_TRAIN_API_URL", "https://api.railwayapi.com/v2/")
    LIVE_TRAIN_API_KEY: str = os.getenv("LIVE_TRAIN_API_KEY", "")
    TRAIN_CACHE_TTL_SECONDS: int = int(os.getenv("TRAIN_CACHE_TTL_SECONDS", "15"))

    # AI Copilot Settings (Sprint AI-FOUNDATION)
    # Set AI_PROVIDER=nvidia to enable NVIDIA NIM live responses.
    # Leave as 'mock' for offline / test operation — no API key required.
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")   # mock | nvidia | anthropic | openai | gemini
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")         # Never hardcode — set in .env only
    AI_MODEL: str = os.getenv("AI_MODEL", "mock-model")    # e.g. meta/llama-3.1-70b-instruct
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")        # Override base URL (NVIDIA: https://integrate.api.nvidia.com/v1)

    # Security & CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip():
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ]

settings = Settings()
