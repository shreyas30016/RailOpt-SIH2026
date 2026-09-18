from fastapi import APIRouter, Depends
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.schemas import WhatIfRequest
from ..optimizer.whatif import WhatIfSimulator
from .auth import require_permission

router = APIRouter(prefix="/whatif", tags=["What-If Simulation"])


@router.post("/simulate")
def simulate_scenario(
    request: WhatIfRequest,
    current_user: dict = Depends(require_permission("can_optimize")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run a What-if disruption scenario and return full before/after comparison.
    Supports: TRAIN_DELAY, MAINTENANCE_OVERRUN, BLOCK_UNAVAILABLE, EMERGENCY_JOB
    """
    simulator = WhatIfSimulator(db)
    result = simulator.simulate_scenario(request)
    return result
