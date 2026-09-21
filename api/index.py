import os
import sys
from pathlib import Path

# Explicitly mark serverless runtime and disable browser popping
os.environ["VERCEL"] = "1"
os.environ["NO_AUTO_BROWSER"] = "1"

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from backend.app.main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    
    app = FastAPI()
    err_msg = traceback.format_exc()
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    async def catch_all(path: str):
        return PlainTextResponse(f"Vercel Serverless Import Error:\n\n{err_msg}", status_code=500)
