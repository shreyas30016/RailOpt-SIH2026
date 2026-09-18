import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def test_vercel_simulation():
    # 1. Set environment variable to simulate Vercel
    os.environ["VERCEL"] = "1"
    
    # 2. Check that database URL resolves to /tmp/railopt.db
    from backend.app.config import settings, get_default_database_url
    db_url = get_default_database_url()
    print("[1] Vercel DATABASE_URL resolution:", db_url)
    assert db_url == "sqlite:////tmp/railopt.db", f"Expected /tmp/railopt.db, got {db_url}"
    
    # 3. Import FastAPI app from main.py and api/index.py
    from backend.app.main import app as main_app
    from api.index import app as index_app
    print("[2] Successfully imported main_app and index_app without side effects!")
    assert main_app is not None
    assert index_app is not None
    assert main_app == index_app
    
    # 4. Test client without error
    from fastapi.testclient import TestClient
    client = TestClient(main_app)
    health = client.get("/health")
    print("[3] /health response in serverless simulation:", health.status_code, health.json())
    assert health.status_code == 200
    
    print("[SUCCESS] All Vercel serverless simulation assertions passed!")

if __name__ == "__main__":
    test_vercel_simulation()
