"""
P1.4 / Reports Dynamic & Grounded Analytics Test Suite
======================================================
Tests mathematical integrity, dynamic filtering (division, section, department),
role-based scoping, and dataset exports for /api/reports/analytics.
"""

import pytest
import base64
import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def _auth_header(role: str, division_code: str = "NDL") -> dict:
    tok_data = {"role": role, "division_code": division_code}
    token = base64.b64encode(json.dumps(tok_data).encode()).decode()
    return {"Authorization": f"Bearer {token}"}


def test_reports_analytics_kpi_mathematical_bounds():
    """Verify that all KPIs are within mathematically realistic boundaries."""
    resp = client.get("/api/reports/analytics", headers=_auth_header("CONTROLLER"))
    assert resp.status_code == 200
    data = resp.json()
    kpis = data["kpis"]

    # Completion / Grant ratio must be bounded <= 100% and >= 0%
    assert 0.0 <= kpis["job_completion_rate_pct"] <= 100.0, f"Unrealistic completion rate: {kpis['job_completion_rate_pct']}"
    assert 0.0 <= kpis["average_grant_ratio_pct"] <= 100.0, f"Unrealistic grant ratio: {kpis['average_grant_ratio_pct']}"

    # Block utilization must be bounded <= 100% and > 0%
    assert 0.0 <= kpis["block_utilization_pct"] <= 100.0, f"Unrealistic utilization: {kpis['block_utilization_pct']}"

    # Mean delay per block must be non-negative
    assert kpis["mean_delay_per_block_min"] >= 0.0

    # Safety compliance must be 100.0%
    assert kpis["safety_compliance_pct"] == 100.0

    # Ensure raw records and context exist
    assert "raw_records" in data
    assert len(data["raw_records"]) > 0
    assert "corridor_context" in data
    assert "Delhi" in data["corridor_context"]


def test_reports_analytics_division_filtering():
    """Verify dynamic division filtering (Delhi vs Agra vs ALL)."""
    # 1. Delhi Division
    resp_delhi = client.get("/api/reports/analytics?division=Delhi", headers=_auth_header("CONTROLLER"))
    assert resp_delhi.status_code == 200
    delhi_data = resp_delhi.json()
    assert "Delhi" in delhi_data["corridor_context"]
    assert len(delhi_data["section_statistics"]) == 3
    for s in delhi_data["section_statistics"]:
        assert s["division"] == "Delhi"

    # 2. Agra Division
    resp_agra = client.get("/api/reports/analytics?division=Agra", headers=_auth_header("CONTROLLER"))
    assert resp_agra.status_code == 200
    agra_data = resp_agra.json()
    assert "Agra" in agra_data["corridor_context"]
    assert len(agra_data["section_statistics"]) == 3
    for s in agra_data["section_statistics"]:
        assert s["division"] == "Agra"

    # Total blocks in Delhi + Agra should equal ALL blocks in corridor
    resp_all = client.get("/api/reports/analytics?division=ALL", headers=_auth_header("CONTROLLER"))
    all_data = resp_all.json()
    delhi_blocks = len(delhi_data["raw_records"])
    agra_blocks = len(agra_data["raw_records"])
    all_blocks = len(all_data["raw_records"])
    assert delhi_blocks + agra_blocks == all_blocks


def test_reports_analytics_section_filtering():
    """Verify section filtering correctly scopes department stats and raw records."""
    resp = client.get("/api/reports/analytics?section=NDLS-TKD", headers=_auth_header("CONTROLLER"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["section_statistics"]) == 1
    assert data["section_statistics"][0]["code"] == "NDLS-TKD"
    for r in data["raw_records"]:
        assert r["section"] == "NDLS-TKD"


def test_reports_analytics_department_filtering():
    """Verify department filtering scopes metrics and raw records."""
    resp_eng = client.get("/api/reports/analytics?department=ENG", headers=_auth_header("CONTROLLER"))
    assert resp_eng.status_code == 200
    eng_data = resp_eng.json()
    assert len(eng_data["department_statistics"]) == 1
    assert eng_data["department_statistics"][0]["code"] == "ENG"
    for r in eng_data["raw_records"]:
        assert r["department"] == "ENG"


def test_reports_analytics_role_scoping_field_roles():
    """Verify field roles (Engineer, TRD Officer, S&T Officer) are scoped to their department."""
    # 1. Engineer scoped to ENG
    resp_eng = client.get("/api/reports/analytics", headers=_auth_header("ENGINEER"))
    assert resp_eng.status_code == 200
    data_eng = resp_eng.json()
    assert data_eng["active_filters"]["department"] == "ENG"
    assert len(data_eng["department_statistics"]) == 1
    assert data_eng["department_statistics"][0]["code"] == "ENG"
    for r in data_eng["raw_records"]:
        assert r["department"] == "ENG"

    # 2. TRD Officer scoped to TRD
    resp_trd = client.get("/api/reports/analytics", headers=_auth_header("TRD_OFFICER"))
    assert resp_trd.status_code == 200
    data_trd = resp_trd.json()
    assert data_trd["active_filters"]["department"] == "TRD"
    assert len(data_trd["department_statistics"]) == 1
    assert data_trd["department_statistics"][0]["code"] == "TRD"
    for r in data_trd["raw_records"]:
        assert r["department"] == "TRD"

    # 3. S&T Officer scoped to S_T
    resp_st = client.get("/api/reports/analytics", headers=_auth_header("ST_OFFICER"))
    assert resp_st.status_code == 200
    data_st = resp_st.json()
    assert data_st["active_filters"]["department"] == "S_T"
    assert len(data_st["department_statistics"]) == 1
    assert data_st["department_statistics"][0]["code"] == "S_T"
    for r in data_st["raw_records"]:
        assert r["department"] == "S_T"


def test_reports_analytics_historical_runs_trends():
    """Verify historical runs are returned with valid timestamps and solver metrics."""
    resp = client.get("/api/reports/analytics", headers=_auth_header("CONTROLLER"))
    assert resp.status_code == 200
    data = resp.json()
    runs = data["historical_optimization_runs"]
    assert len(runs) > 0
    top = runs[0]
    assert "run_id" in top
    assert "timestamp" in top
    assert "status" in top
    assert "scheduled" in top
    assert "solver_time_sec" in top
