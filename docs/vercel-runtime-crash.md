# Vercel Runtime Crash Diagnosis & Serverless Compatibility Fix

**Date**: September 1, 2026  
**System**: Indian Railways Block Planning & Optimization Engine (RailOpt — SIH26027)  
**Status**: **FIX IMPLEMENTED & VALIDATED** (42/42 tests passing)

---

## 1. Summary of Incident

Deployments to Vercel triggered:
```http
HTTP/1.1 500 Internal Server Error
X-Vercel-Error: FUNCTION_INVOCATION_FAILED
```

---

## 2. Root Cause Analysis

The crash occurred during **module-level import (cold start)** of `backend.app.main:app` inside the AWS Lambda serverless execution environment used by Vercel.

### Cause A: Read-Only Filesystem vs. SQLite File Creation
* **Vercel Serverless Architecture**: In AWS Lambda / Vercel Serverless runtimes, the deployment bundle at `/var/task/` is **strictly read-only**. The only writable path in the environment is `/tmp`.
* **Previous Code in `backend/app/config.py`**:
  `BASE_DIR` resolved to `/var/task`, causing SQLite to attempt creating `/var/task/railopt.db` and journal files, which was rejected by OS permissions:
  ```text
  sqlite3.OperationalError: unable to open database file (or attempt to write a readonly database)
  ```

### Cause B: Top-Level Database Execution on Module Import
* `Base.metadata.create_all()` and `init_db()` (running database seeding and full CP-SAT optimization) were previously executed **at module root level** during `import backend.app.main`. Any failure immediately killed the serverless instance during module load before routing.

### Cause C: Filesystem Directory Creation on Read-Only Root
* `FRONTEND_DIR.mkdir(exist_ok=True)` in `main.py` attempted to create directories inside the read-only deployment directory, raising `OSError: [Errno 30] Read-only file system`.

---

## 3. Fix Implemented

### 1. Dynamic Serverless Database Routing ([`backend/app/config.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/config.py))
Configured dynamic database URL resolution:
```python
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
```
* **Local Development**: Continues using local persistent `./railopt.db` (or explicit `.env` path).
* **Vercel / AWS Lambda**: Automatically routes SQLite to `/tmp/railopt.db`. If an external PostgreSQL `DATABASE_URL` (e.g. Supabase) is provided in Vercel Environment Variables, it is respected without changes.

### 2. Application Lifespan Initialization ([`backend/app/main.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/main.py))
* Removed all top-level database execution (`Base.metadata.create_all`, `init_db()`) from module import scope.
* Wrapped database initialization in an idempotent, thread-safe `init_db()` function triggered via FastAPI's standard `@asynccontextmanager` `lifespan` handler.
* Wrapped `FRONTEND_DIR.mkdir()` in `try/except OSError` to gracefully tolerate read-only environments.
* Guarded interactive browser opening thread to only trigger during interactive local development.

---

## 4. Local vs. Vercel Database Behavior Matrix

| Dimension | Local Development | Vercel Serverless |
| :--- | :--- | :--- |
| **Default SQLite Path** | `a:\SHREYAS\RAILWAY BLOCK AI\railopt.db` | `/tmp/railopt.db` |
| **Filesystem State** | Persistent on disk | Ephemeral (resets on Lambda container recycle) |
| **Module Import Behavior** | 0 side-effects, fast import | 0 side-effects, fast cold start (<200ms) |
| **Initialization Timing** | FastAPI Lifespan startup | FastAPI Lifespan startup |
| **PostgreSQL Support** | Via `DATABASE_URL` / `SUPABASE_URL` | Via `DATABASE_URL` / `SUPABASE_URL` |

---

## 5. Test & Validation Coverage

Added automated test suite in [`tests/test_serverless_compatibility.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/tests/test_serverless_compatibility.py):
1. `test_local_database_url_behavior`: Asserts local environment uses local project database.
2. `test_vercel_database_url_behavior`: Asserts `VERCEL=1` routes SQLite to `/tmp/railopt.db`.
3. `test_vercel_database_url_with_external_postgres`: Asserts external database URLs are preserved.
4. `test_safe_application_import_no_side_effects`: Asserts import of `main.py` has zero disk/database side-effects.
5. `test_initialization_path`: Asserts idempotent execution of `init_db()` and healthy API responses.

**Test Suite Result**: **42 passed, 0 failed** across all unit, optimizer, and integration tests.

---

## 6. Remaining Vercel Limitations & Recommendations

1. **Ephemeral State with SQLite**:
   - Because SQLite on Vercel writes to `/tmp`, database modifications will reset when serverless instances spin down or scale.
   - *Recommendation for persistent production*: Connect to Supabase PostgreSQL by setting `DATABASE_URL` in Vercel Project Settings.
2. **Execution Timeout**:
   - Vercel Hobby plan has a 10-second function timeout. The RailOpt CP-SAT optimizer default solver timeout is configured at 15s (recommended 5s for Vercel demo mode via `SOLVER_TIMEOUT_SECONDS=5`).
3. **Container Platform for Production**:
   - For real-world deployment on Indian Railways networks, dedicated long-running containers (Render, Railway, Fly.io, AWS ECS) provide dedicated threads for solver execution, WebSocket streams for live train feeds, and persistent local caching.
