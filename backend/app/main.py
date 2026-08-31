import os
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

# 1. Create database tables
Base.metadata.create_all(bind=engine)

# 2. Seed data and initial run on startup
def init_db():
    db = SessionLocal()
    try:
        seed_synthetic_data(db)
        # Check if an optimization run exists; if not, run one
        if db.query(OptimizationRun).count() == 0:
            optimizer = RailwayBlockOptimizer(db)
            optimizer.run_optimization()
    finally:
        db.close()

init_db()

import webbrowser
import threading
import time

# 3. Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Deterministic Railway Block Planning and Optimization Engine for Indian Railways (SIH 2026 SIH26027)"
)

def auto_open_browser():
    time.sleep(1.2)
    try:
        webbrowser.open("http://127.0.0.1:8000/dashboard")
    except Exception as e:
        print(f"[*] Open browser at http://127.0.0.1:8000/dashboard: {e}")

@app.on_event("startup")
def on_startup():
    # Automatically open the browser on local runs
    if os.getenv("NO_AUTO_BROWSER", "").lower() not in ("1", "true", "yes"):
        threading.Thread(target=auto_open_browser, daemon=True).start()

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
FRONTEND_DIR.mkdir(exist_ok=True)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.get("/")
def read_root():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

@app.get("/dashboard")
def get_dashboard_page():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

@app.get("/maintenance-requests")
def get_maintenance_page():
    return FileResponse(str(FRONTEND_DIR / "maintenance-requests.html"))

@app.get("/block-planning")
def get_planning_page():
    return FileResponse(str(FRONTEND_DIR / "block-planning.html"))

@app.get("/gantt-view")
def get_gantt_page():
    return FileResponse(str(FRONTEND_DIR / "gantt-view.html"))

@app.get("/what-if")
def get_whatif_page():
    return FileResponse(str(FRONTEND_DIR / "what-if.html"))

@app.get("/constraints-logic")
def get_constraints_page():
    return FileResponse(str(FRONTEND_DIR / "constraints-logic.html"))

@app.get("/reports")
def get_reports_page():
    return FileResponse(str(FRONTEND_DIR / "reports.html"))

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
