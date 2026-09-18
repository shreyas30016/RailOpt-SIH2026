import pytest
from backend.app.services.train_adapter import (
    TrainDataAdapter,
    MockTrainDataProvider,
    LiveTrainDataProvider,
    NormalizedTrainMovement
)

def test_mock_train_provider():
    provider = MockTrainDataProvider()
    movements = provider.get_live_train_movements()
    
    assert len(movements) >= 5
    vande_bharat = next((m for m in movements if m.train_id == "22436"), None)
    assert vande_bharat is not None
    assert vande_bharat.train_type == "VANDE_BHARAT"
    assert vande_bharat.source == "Synthetic Demo Data"
    assert vande_bharat.delay_minutes == 0

def test_train_delay_normalization():
    provider = MockTrainDataProvider()
    provider.set_simulated_delay("12050", 25)
    
    gatimaan = provider.get_train_status("12050")
    assert gatimaan is not None
    assert gatimaan.delay_minutes == 25
    assert gatimaan.status == "DELAYED"
    assert gatimaan.estimated_departure_min == gatimaan.scheduled_departure_min + 25

def test_live_provider_fallback_on_unconfigured_or_error():
    # Live provider without key or on network error must raise ConnectionError
    live_prov = LiveTrainDataProvider(api_url="http://invalid-train-api.local", api_key="")
    with pytest.raises(ConnectionError):
        live_prov.get_live_train_movements()

def test_train_data_adapter_automatic_fallback():
    adapter = TrainDataAdapter()
    result = adapter.get_movements(force_refresh=True)
    
    assert "source" in result
    assert "movements" in result
    assert len(result["movements"]) > 0
    # Must fall back gracefully to Synthetic Demo Data when live API not present
    assert result["is_fallback"] is True

def test_train_delay_simulation_via_adapter():
    adapter = TrainDataAdapter()
    res = adapter.simulate_delay("22436", 15)
    
    vb = next((m for m in res["movements"] if m["train_id"] == "22436"), None)
    assert vb is not None
    assert vb["delay_minutes"] == 15
    assert vb["status"] == "DELAYED"


def test_replay_payload_metadata_and_phases():
    from collections import Counter
    adapter = TrainDataAdapter()
    result = adapter.get_movements(force_refresh=True)
    assert result["mode"] == "timetable_replay"
    assert result["timezone"] == "Asia/Kolkata"
    assert result["as_of"]
    assert "phase" in result["movements"][0]
    phases = Counter(m["phase"] for m in result["movements"])
    # Fleet is scheduled so that several trains are always active at any hour
    assert phases.get("RUNNING", 0) + phases.get("PRE_DEP", 0) >= 2, phases


def test_replay_movement_advances_and_delay_drift_is_bounded():
    import time
    p1 = MockTrainDataProvider()
    m1 = {m.train_id: m for m in p1.get_live_train_movements()}
    time.sleep(1.5)
    m2 = {m.train_id: m for m in p1.get_live_train_movements()}
    running = [tid for tid, m in m1.items() if m.phase == "RUNNING"]
    assert running, "expected at least one running train in the replay"
    # Positions of a running train must never go backwards and must advance over time
    for tid in running:
        a, b = m1[tid].progress_pct, m2[tid].progress_pct
        assert 0.0 <= a <= 100.0 and 0.0 <= b <= 100.0
        assert b >= a
    # Any delay drift for an on-time (base 0) premium train stays zero
    vb = m1["22436"]
    assert vb.delay_minutes == 0 and vb.status == "ON_TIME"


def test_replay_source_label_always_disclosed():
    adapter = TrainDataAdapter()
    result = adapter.get_movements(force_refresh=True)
    assert "Synthetic" in result["source"] or "Live" in result["source"]
    assert result["is_simulated"] is True  # no live provider configured in tests
