import os
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

def test_local_database_url_behavior(monkeypatch):
    """Ensure that in local environment without VERCEL=1, persistent SQLite path is used."""
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.delenv("LAMBDA_TASK_ROOT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from backend.app.config import get_default_database_url, BASE_DIR
    db_url = get_default_database_url()
    assert str(BASE_DIR) in db_url or "railopt.db" in db_url
    assert not db_url.startswith("sqlite:////tmp/")

def test_vercel_database_url_behavior(monkeypatch):
    """Ensure that in Vercel/serverless environment, SQLite routes to /tmp/railopt.db."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from backend.app.config import get_default_database_url
    db_url = get_default_database_url()
    assert db_url == "sqlite:////tmp/railopt.db"

def test_vercel_database_url_with_external_postgres(monkeypatch):
    """Ensure that if an external PostgreSQL database is configured on Vercel, it is preserved."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.supabase.co:5432/railopt")

    from backend.app.config import get_default_database_url
    db_url = get_default_database_url()
    assert db_url == "postgresql://user:pass@db.supabase.co:5432/railopt"

def test_safe_application_import_no_side_effects():
    """Verify that importing main.py does not raise exceptions or perform unwanted filesystem operations."""
    from backend.app.main import app, init_db, _db_initialized
    assert app is not None
    assert app.title == "Indian Railways Block Planning & Optimization (RailOpt)"

def test_initialization_path():
    """Verify that init_db() executes idempotently and seeds the database correctly."""
    from backend.app.main import app, init_db
    init_db()
    
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    
    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    assert dash_res.json()["total_jobs"] > 0
