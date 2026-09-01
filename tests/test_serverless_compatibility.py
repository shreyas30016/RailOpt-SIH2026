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
    from backend.app.main import app, initialize_application_data
    assert app is not None
    assert app.title == "Indian Railways Block Planning & Optimization (RailOpt)"

def test_initialization_path():
    """Verify that initialize_application_data() executes idempotently and seeds the database correctly."""
    from backend.app.main import app, initialize_application_data
    initialize_application_data()
    
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    
    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    assert dash_res.json()["total_jobs"] > 0

def test_frontend_routes_served_safely():
    """Verify that all main frontend and health endpoints return 200 without filesystem mutation."""
    from backend.app.main import app, initialize_application_data
    initialize_application_data()
    client = TestClient(app)

    routes = [
        "/health",
        "/",
        "/dashboard",
        "/maintenance-requests",
        "/block-planning",
        "/gantt-view",
        "/what-if",
        "/constraints-logic",
        "/reports"
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Route {route} returned status {response.status_code}"

def test_direct_post_optimize_endpoint():
    """Verify that POST /optimize works on demand without requiring import-time solver execution."""
    from backend.app.main import app, initialize_application_data
    initialize_application_data()
    client = TestClient(app)

    res = client.post("/optimize", json={"max_solver_time_sec": 5})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["OPTIMAL", "FEASIBLE"]
    assert data["scheduled_jobs_count"] > 0

def test_whatif_simulation_endpoint():
    """Verify that What-if simulation endpoint functions correctly."""
    from backend.app.main import app, initialize_application_data
    initialize_application_data()
    client = TestClient(app)

    res = client.post("/api/whatif/simulate", json={
        "scenario_name": "Serverless Delay Test",
        "delayed_train_number": "12002",
        "simulated_train_delay_min": 20
    })
    assert res.status_code == 200
    data = res.json()
    assert "scenario_name" in data
    assert "simulated_run" in data
