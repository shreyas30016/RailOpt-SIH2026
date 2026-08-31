from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class JobConstraintMeta:
    job_id: int
    job_code: str
    department_code: str
    section_code: str
    track_line_code: str
    duration_min: int
    priority: int
    urgency: str
    requires_power_block: bool
    requires_traffic_block: bool
    requires_speed_restriction: bool
    speed_restriction_kmh: int
    required_resource_code: str
    earliest_start_min: int
    latest_end_min: int
    preceding_job_code: Optional[str] = None # Precedence dependency: must run after preceding_job

@dataclass
class TrainConstraintMeta:
    train_number: str
    train_name: str
    train_type: str
    priority_weight: int
    direction: str
    departure_min: int
    arrival_min: int
    sections_traversed: List[str]

class RailwayConstraintManager:
    """
    Modular constraint configuration manager for Indian Railways block scheduling.
    Allows enabling/disabling or tuning weights for specific railway operating rules.
    Every unvalidated operational rule is marked as PROTOTYPE ASSUMPTION / NEEDS DOMAIN VALIDATION.
    """
    def __init__(
        self,
        enable_power_block_coupling: bool = True,
        enable_shadow_block_synergy: bool = True,
        enable_machine_exclusivity: bool = True,
        enable_job_precedence: bool = True,
        enable_headway_margins: bool = True,
        headway_margin_minutes: int = 3, # [PROTOTYPE ASSUMPTION / NEEDS DOMAIN VALIDATION]
        max_allowed_train_delay_min: int = 45,
        shadow_block_bonus_weight: int = 4000,
        train_delay_penalty_multiplier: int = 10,
        department_compatibility: Optional[Dict[str, List[str]]] = None
    ):
        self.enable_power_block_coupling = enable_power_block_coupling
        self.enable_shadow_block_synergy = enable_shadow_block_synergy
        self.enable_machine_exclusivity = enable_machine_exclusivity
        self.enable_job_precedence = enable_job_precedence
        self.enable_headway_margins = enable_headway_margins
        self.headway_margin_minutes = headway_margin_minutes
        self.max_allowed_train_delay_min = max_allowed_train_delay_min
        self.shadow_block_bonus_weight = shadow_block_bonus_weight
        self.train_delay_penalty_multiplier = train_delay_penalty_multiplier

        # Configurable Department Compatibility Matrix for Shadow Block Co-Location
        # [PROTOTYPE ASSUMPTION / NEEDS DOMAIN VALIDATION]
        self.dept_compatibility = department_compatibility or {
            "ENG": ["TRD", "S_T", "MECH"],
            "TRD": ["ENG", "S_T", "MECH"],
            "S_T": ["ENG", "TRD", "MECH"],
            "MECH": ["ENG", "TRD", "S_T"]
        }

    def can_form_shadow_block(self, job_a: JobConstraintMeta, job_b: JobConstraintMeta) -> bool:
        """
        Determines whether two maintenance jobs can safely share a combined shadow block.
        Engineering + Traction (OHE) + S&T on the same section & track line can form a shadow block.
        Two jobs from the SAME department requiring the SAME track line spot cannot shadow-block each other.
        """
        if not self.enable_shadow_block_synergy:
            return False

        if job_a.section_code != job_b.section_code or job_a.track_line_code != job_b.track_line_code:
            return False
        
        # Check configurable department compatibility matrix
        allowed_peers = self.dept_compatibility.get(job_a.department_code, [])
        return job_b.department_code in allowed_peers
