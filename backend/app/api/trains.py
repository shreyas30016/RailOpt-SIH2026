from fastapi import APIRouter, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..services.train_adapter import train_adapter

router = APIRouter(prefix="/trains", tags=["Live Train Data"])

class SimulateDelayRequest(BaseModel):
    train_id: str
    delay_minutes: int

@router.get("/live")
def get_live_train_movements(force_refresh: bool = Query(False, description="Bypass cache and force refresh")):
    """
    Returns normalized train movements from live/public feed with automatic mock fallback.
    """
    return train_adapter.get_movements(force_refresh=force_refresh)

@router.get("/status/{train_id}")
def get_train_status(train_id: str):
    data = train_adapter.get_movements()
    for m in data.get("movements", []):
        if m.get("train_id") == train_id:
            return {
                "source": data.get("source"),
                "movement": m
            }
    return {
        "source": data.get("source"),
        "error": f"Train {train_id} not found in current corridor window."
    }

@router.post("/simulate-delay")
def simulate_train_delay(req: SimulateDelayRequest):
    """
    Simulates a live train delay event to feed the maintenance-block replanner.
    """
    return train_adapter.simulate_delay(req.train_id, req.delay_minutes)
