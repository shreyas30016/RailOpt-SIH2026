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
