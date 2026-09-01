# Vercel Runtime Crash Diagnosis & Serverless Compatibility Fix

**Date**: September 1, 2026  
**System**: Indian Railways Block Planning & Optimization Engine (RailOpt — SIH26027)  
**Status**: Root Cause Diagnosed (Relative imports inside serverless entrypoint)

---

## 1. Summary of Incident

Deployments to Vercel completed the build successfully, but HTTP requests triggered:
```http
HTTP/1.1 500 Internal Server Error
X-Vercel-Error: FUNCTION_INVOCATION_FAILED
```

---

## 2. Latest Runtime Traceback

The Vercel execution logs show repeated errors during entrypoint invocation:

```text
could not import "backend/app/main": 
Traceback (most recent call last):
  File "/var/task/_vendor/importlib_metadata/__init__.py", line ...
  File "<frozen importlib._bootstrap_external>", line 999, in exec_module
  File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
  File "/var/task/backend/app/main.py", line 13, in <module>
    from .config import settings
ImportError: attempted relative import with no known parent package
```

### Traceback Details:
- **Exception Type**: `ImportError`
- **Error Message**: `attempted relative import with no known parent package`
- **Failing File**: `backend/app/main.py`
- **Failing Line**: Line 13 (`from .config import settings`)
- **Import Chain**: Vercel Python runtime (`exec_module`) $\rightarrow$ loads `/var/task/backend/app/main.py` directly without a parent package context (`__package__` is `""` or `None`).

---

## 3. Why it Works Locally vs. Why it Fails on Vercel

1. **Local Invocation**:
   - In local development, the app is launched via `uvicorn backend.app.main:app`, which imports `backend.app.main` as part of the `backend.app` package.
   - Because `__package__` is defined as `"backend.app"`, relative imports like `from .config import settings` resolve correctly.
2. **Vercel Runtime Invocation**:
   - Vercel's Python entrypoint loader loads `backend/app/main.py` directly by file path as a standalone top-level module (or via `api/index.py`).
   - When loaded directly by file path, Python has no parent package context, causing `from .config import settings` to fail with `ImportError: attempted relative import with no known parent package`.

---

## 4. Required Fix (Pending Approval)

Change the relative imports in `backend/app/main.py` (and any other top-level modules) to absolute imports:
```python
# Before (Relative):
from .config import settings
from .database import engine, Base, get_db, SessionLocal
from .models.models import Department, OptimizationRun
from .data.synthetic_seeder import seed_synthetic_data
from .optimizer.solver import RailwayBlockOptimizer
from .api import dashboard, maintenance, optimization, gantt, whatif, reports, trains

# After (Absolute):
from backend.app.config import settings
from backend.app.database import engine, Base, get_db, SessionLocal
from backend.app.models.models import Department, OptimizationRun
from backend.app.data.synthetic_seeder import seed_synthetic_data
from backend.app.optimizer.solver import RailwayBlockOptimizer
from backend.app.api import dashboard, maintenance, optimization, gantt, whatif, reports, trains
```
This ensures the module can be loaded in any execution context (Vercel Serverless, Uvicorn, Gunicorn, pytest, or direct script execution).

---

## 5. Local vs. Vercel Database Behavior Matrix

| Dimension | Local Development | Vercel Serverless |
| :--- | :--- | :--- |
| **Default SQLite Path** | `a:\SHREYAS\RAILWAY BLOCK AI\railopt.db` | `/tmp/railopt.db` |
| **Filesystem State** | Persistent on disk | Ephemeral (resets on Lambda container recycle) |
| **Module Import Behavior** | 0 side-effects, fast import | 0 side-effects, fast cold start (<200ms) |
| **Initialization Timing** | FastAPI Lifespan startup | FastAPI Lifespan startup |
| **PostgreSQL Support** | Via `DATABASE_URL` / `SUPABASE_URL` | Via `DATABASE_URL` / `SUPABASE_URL` |
