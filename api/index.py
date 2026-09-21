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

from backend.app.main import app
