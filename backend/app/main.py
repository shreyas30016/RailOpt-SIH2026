import os
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .config import settings
from .database import engine, Base, get_db, SessionLocal
from .models.models import Department, OptimizationRun
from .data.synthetic_seeder import seed_synthetic_data
from .optimizer.solver import RailwayBlockOptimizer

from .api import dashboard, maintenance, optimization, gantt, whatif, reports, trains

# Thread-safe initialization state
_init_lock = threading.Lock()
_db_initialized = False

def init_db():
    """Initializes tables, seeds synthetic data, and performs initial baseline optimization."""
    global _db_initialized
    with _init_lock:
        if _db_initialized:
            return
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_synthetic_data(db)
            if db.query(OptimizationRun).count() == 0:
                optimizer = RailwayBlockOptimizer(db)
                optimizer.run_optimization()
            _db_initialized = True
        finally:
            db.close()

def auto_open_browser():
    time.sleep(1.2)
    try:
        webbrowser.open("http://127.0.0.1:8000/dashboard")
    except Exception as e:
        print(f"[*] Open browser at http://127.0.0.1:8000/dashboard: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB safely on startup (NOT during module import)
    init_db()
    
    # 2. Automatically open browser on interactive local runs
    is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))
    if not is_serverless and os.getenv("NO_AUTO_BROWSER", "").lower() not in ("1", "true", "yes"):
        threading.Thread(target=auto_open_browser, daemon=True).start()
    yield

# 3. Create FastAPI app with lifespan handler
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Deterministic Railway Block Planning and Optimization Engine for Indian Railways (SIH 2026 SIH26027)",
    lifespan=lifespan
)

# 4. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include API Routers
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(maintenance.router, prefix=settings.API_V1_STR)
app.include_router(optimization.router, prefix=settings.API_V1_STR)
app.include_router(gantt.router, prefix=settings.API_V1_STR)
app.include_router(whatif.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(trains.router, prefix=settings.API_V1_STR)

# Direct root aliases
@app.post("/optimize")
def direct_optimize(req: optimization.OptimizeRequest = optimization.OptimizeRequest(), db: Session = Depends(get_db)):
    return optimization.optimize_block_plan(req, db)

# 6. Static files and Frontend routing
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
try:
    FRONTEND_DIR.mkdir(exist_ok=True)
except OSError:
    pass

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

def _serve_frontend_page(filename: str):
    file_path = FRONTEND_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path))
    return {"status": "ok", "message": f"{filename} not found in frontend directory"}

@app.get("/")
def read_root():
    return _serve_frontend_page("dashboard.html")

@app.get("/dashboard")
def get_dashboard_page():
    return _serve_frontend_page("dashboard.html")

@app.get("/maintenance-requests")
def get_maintenance_page():
    return _serve_frontend_page("maintenance-requests.html")

@app.get("/block-planning")
def get_planning_page():
    return _serve_frontend_page("block-planning.html")

@app.get("/gantt-view")
def get_gantt_page():
    return _serve_frontend_page("gantt-view.html")

@app.get("/what-if")
def get_whatif_page():
    return _serve_frontend_page("what-if.html")

@app.get("/constraints-logic")
def get_constraints_page():
    return _serve_frontend_page("constraints-logic.html")

@app.get("/reports")
def get_reports_page():
    return _serve_frontend_page("reports.html")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
