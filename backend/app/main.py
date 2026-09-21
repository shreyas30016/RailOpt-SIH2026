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

from backend.app.config import settings
from backend.app.database import engine, Base, get_db, SessionLocal
from backend.app.models.models import Department, OptimizationRun
from backend.app.data.synthetic_seeder import seed_synthetic_data

from backend.app.api import dashboard, maintenance, optimization, gantt, whatif, reports, trains, auth, ai_chat

# Thread-safe initialization state
_init_lock = threading.Lock()
_db_initialized = False

def initialize_application_data(force: bool = False):
    """
    Safely creates required database tables and seeds synthetic demo data idempotently.
    Never executes mathematical optimization or destructive actions during module import.
    """
    global _db_initialized
    with _init_lock:
        if _db_initialized and not force:
            return
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_synthetic_data(db, force=force)
            _db_initialized = True
        finally:
            db.close()

# Alias for backwards compatibility
init_db = initialize_application_data

def auto_open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000/login"
    try:
        opened = webbrowser.open(url)
        if not opened and os.name == "nt":
            os.system(f'start "" "{url}"')
    except Exception:
        if os.name == "nt":
            try:
                os.system(f'start "" "{url}"')
            except Exception as e:
                print(f"[*] Open browser at {url}: {e}")
        else:
            print(f"[*] Open browser at {url}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB safely on application startup (NOT during module import)
    try:
        initialize_application_data()
    except Exception as e:
        print(f"[!] Warning: Application startup initialization notice: {e}")
    
    # 2. Automatically open browser only on interactive local runs
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
cors_origins = settings.cors_origins_list
has_wildcard = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=not has_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All responses must revalidate — otherwise browsers can serve stale HTML/JS/CSS
# after a deploy (caused silent "old module" behaviour during QA). This is a
# live-data dashboard, so no-cache is the correct default for every route.
@app.middleware("http")
async def no_cache_all_responses(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache"
    return response

# 5. Include API Routers (Mount on both settings.API_V1_STR = "/api" and "/api/v1")
for prefix in (settings.API_V1_STR, "/api/v1"):
    app.include_router(auth.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(maintenance.router, prefix=prefix)
    app.include_router(optimization.router, prefix=prefix)
    app.include_router(gantt.router, prefix=prefix)
    app.include_router(whatif.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(trains.router, prefix=prefix)
    app.include_router(ai_chat.router, prefix=prefix)  # AI Copilot — Sprint AI-FOUNDATION

# Direct root aliases
@app.post("/optimize")
def direct_optimize(
    req: optimization.OptimizeRequest = optimization.OptimizeRequest(),
    current_user: dict = Depends(auth.require_permission("can_optimize")),
    db: Session = Depends(get_db)
):
    return optimization.optimize_block_plan(req, current_user, db)

# 6. Static files and Frontend routing (Safe read-only resolution)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

def _serve_frontend_page(filename: str):
    file_path = FRONTEND_DIR / filename
    if file_path.is_file():
        return FileResponse(str(file_path))
    return {"status": "ok", "message": f"{filename} not found in frontend directory"}

@app.get("/")
def read_root():
    return _serve_frontend_page("login.html")

@app.get("/login")
def get_login_page():
    return _serve_frontend_page("login.html")

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
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/api/docs", include_in_schema=False)
def api_docs():
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title=f"{settings.PROJECT_NAME} - API Docs")

@app.get("/api/openapi.json", include_in_schema=False)
def api_openapi():
    return app.openapi()

