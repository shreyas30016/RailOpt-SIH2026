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
    TRAIN_CACHE_TTL_SECONDS: int = int(os.getenv("TRAIN_CACHE_TTL_SECONDS", "60"))

settings = Settings()
