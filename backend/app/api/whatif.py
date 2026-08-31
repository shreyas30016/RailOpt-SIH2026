from fastapi import APIRouter, Depends
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.schemas import WhatIfRequest
from ..optimizer.whatif import WhatIfSimulator

router = APIRouter(prefix="/whatif", tags=["What-If Simulation"])


@router.post("/simulate")
def simulate_scenario(request: WhatIfRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Run a What-if disruption scenario and return full before/after comparison.
    Supports: TRAIN_DELAY, MAINTENANCE_OVERRUN, BLOCK_UNAVAILABLE, EMERGENCY_JOB
    """
    simulator = WhatIfSimulator(db)
    result = simulator.simulate_scenario(request)
    return result
