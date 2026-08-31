from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.schemas import WhatIfRequest, WhatIfComparisonResponse
from ..optimizer.whatif import WhatIfSimulator

router = APIRouter(prefix="/whatif", tags=["What-If Simulation"])

@router.post("/simulate", response_model=WhatIfComparisonResponse)
def simulate_scenario(request: WhatIfRequest, db: Session = Depends(get_db)):
    simulator = WhatIfSimulator(db)
    result = simulator.simulate_scenario(request)
    return result
