from fastapi import APIRouter, Depends, Query, Response
from .auth import require_permission
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..database import get_db
from ..models.models import TrainSchedule
from ..services.train_adapter import train_adapter

router = APIRouter(prefix="/trains", tags=["Live Train Data"])

class SimulateDelayRequest(BaseModel):
    train_id: str
    delay_minutes: int

@router.get("/list")
def get_train_list(db: Session = Depends(get_db)):
    """
    Return the corridor train timetable (real DB records) for the What-If
    train selector and Gantt overlays.
    """
    trains = db.query(TrainSchedule).order_by(TrainSchedule.departure_minute.asc()).all()
    return [
        {
            "train_number": t.train_number,
            "train_name": t.train_name,
            "train_type": t.train_type,
            "direction": t.direction,
            "priority_weight": t.priority_weight,
            "origin_station": t.origin_station,
            "destination_station": t.destination_station,
            "departure_minute": t.departure_minute,
            "arrival_minute": t.arrival_minute,
        }
        for t in trains
    ]

@router.get("/live")
def get_live_train_movements(response: Response, force_refresh: bool = Query(False, description="Bypass cache and force refresh")):
    """
    Returns normalized train movements from live/public feed with automatic mock fallback.
    """
    data = train_adapter.get_movements(force_refresh=force_refresh)
    
    # Filter out IDLE trains to reduce payload bloat
    if "movements" in data:
        data["movements"] = [m for m in data["movements"] if m.get("phase") != "IDLE"]
        
    response.headers["Cache-Control"] = "public, max-age=10"
    return data

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
def simulate_train_delay(
    req: SimulateDelayRequest,
    current_user: dict = Depends(require_permission("can_optimize")),
):
    """
    Simulates a live train delay event to feed the maintenance-block replanner.
    """
    return train_adapter.simulate_delay(req.train_id, req.delay_minutes)
