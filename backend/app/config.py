import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "Indian Railways Block Planning & Optimization (RailOpt)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/railopt.db")
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
