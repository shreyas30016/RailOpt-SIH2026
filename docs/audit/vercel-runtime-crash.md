# Vercel Runtime Crash Diagnosis & Serverless Compatibility Audit

**Date**: September 1, 2026  
**System**: Indian Railways Block Planning & Optimization Engine (RailOpt — SIH26027)  
**Status**: **RESOLVED & TESTED** (45/45 tests passing, 0 import side-effects)

---

## 1. Confirmed Original Failure

Deployments to Vercel triggered:
```http
HTTP/1.1 500 Internal Server Error
X-Vercel-Error: FUNCTION_INVOCATION_FAILED
```

### Exact Traceback & Root Cause:
1. **Direct File Loader vs. Relative Imports**:
   ```text
   could not import "backend/app/main": 
   File "<frozen importlib._bootstrap_external>", line 999, in exec_module
   File "/var/task/backend/app/main.py", line 13, in <module>
     from .config import settings
   ImportError: attempted relative import with no known parent package
   ```
2. **Import-Time Filesystem & Optimization Execution**:
   - `Base.metadata.create_all()` attempting to write to `/var/task/railopt.db` (read-only filesystem on AWS Lambda).
   - Top-level `optimizer.run_optimization()` running Google OR-Tools during module load on every cold start.
   - `FRONTEND_DIR.mkdir()` attempting filesystem writes during module import.

---

## 2. Comprehensive Import-Time Audit & Changes Made

| File | Previous Problematic Behavior | Refactored Serverless Safe Implementation |
| :--- | :--- | :--- |
| **`backend/app/config.py`** | Hardcoded default database path to `/var/task/railopt.db` | `get_default_database_url()` routes SQLite to `/tmp/railopt.db` when `VERCEL=1` is present; preserves local path locally; preserves external PostgreSQL when `DATABASE_URL` is set. |
| **`backend/app/main.py`** | 1. Relative imports (`from .config`)<br>2. Top-level `create_all()` and `init_db()` running solver at import<br>3. `FRONTEND_DIR.mkdir()` | 1. Converted to absolute imports (`from backend.app...`)<br>2. Replaced with `initialize_application_data()` inside FastAPI `lifespan` without optimizer execution on import<br>3. Replaced `mkdir` with safe read-only existence check (`if FRONTEND_DIR.is_dir():`). |
| **`backend/app/database.py`** | Relative import of settings | Absolute import with fallback; creates SQLAlchemy engine with zero import-time disk connections. |
| **`api/index.py`** | Custom entrypoint setup | Clean standard entrypoint re-exporting `from backend.app.main import app`. |
| **`pyproject.toml`** | Standard PEP 621 metadata | Validated `[project]` table with Python 3.12 compatibility and `[tool.vercel] entrypoint = "backend.app.main:app"`. |

---

## 3. Database Behavior Matrix

| Dimension | Local Development | Vercel Serverless |
| :--- | :--- | :--- |
| **Default SQLite Path** | `A:\SHREYAS\RAILWAY BLOCK AI\railopt.db` (Persistent) | `/tmp/railopt.db` (Writable partition) |
| **Module Import Execution** | Zero DB writes, zero table creation, zero solver run | Zero DB writes, zero table creation, zero solver run |
| **Initialization Trigger** | On server startup via `lifespan` | On server startup via `lifespan` |
| **Solver Execution** | Only on explicit `POST /optimize` or `/api/optimization/run` | Only on explicit `POST /optimize` or `/api/optimization/run` |
| **PostgreSQL Support** | Supported via `DATABASE_URL` / `SUPABASE_URL` | Supported via `DATABASE_URL` / `SUPABASE_URL` |

---

## 4. Test & Verification Summary

1. **Vercel Simulation (`scratch/test_vercel_simulation.py`)**:
   - `VERCEL=1` verified: `DATABASE_URL` resolves to `sqlite:////tmp/railopt.db`.
   - `import backend.app.main` and `import api.index` executed with zero side effects.
2. **Local Regression Suite (`tests/test_serverless_compatibility.py`)**:
   - `test_local_database_url_behavior` $\rightarrow$ Passed
   - `test_vercel_database_url_behavior` $\rightarrow$ Passed
   - `test_vercel_database_url_with_external_postgres` $\rightarrow$ Passed
   - `test_safe_application_import_no_side_effects` $\rightarrow$ Passed
   - `test_initialization_path` $\rightarrow$ Passed
   - `test_frontend_routes_served_safely` $\rightarrow$ Passed
   - `test_direct_post_optimize_endpoint` $\rightarrow$ Passed
   - `test_whatif_simulation_endpoint` $\rightarrow$ Passed
3. **Full Pytest Suite**:
   **45 passed, 0 failed** across all test modules in 4.02s.

---

## 5. Remaining Serverless Limitations & Production Recommendations

1. **Ephemeral SQLite**:
   - On Vercel, SQLite database is stored in `/tmp/railopt.db`, which is wiped when serverless containers cycle.
   - *For persistent cloud production*: Connect a PostgreSQL database (e.g. Supabase) by setting `DATABASE_URL` in Vercel environment variables.
2. **Solver Execution Timeouts**:
   - Vercel Hobby plan has a 10s maximum execution limit. The RailOpt CP-SAT solver default is 15s (`SOLVER_TIMEOUT_SECONDS=15`). For Vercel demo, set `SOLVER_TIMEOUT_SECONDS=5` in project environment variables if needed.
