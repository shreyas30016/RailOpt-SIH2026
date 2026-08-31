from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from .rules_loader import rules_loader

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
    Pulls configurable operating parameters, buffers, bounds, and weights from backend/config/railway_rules.yaml.
    """
    def __init__(
        self,
        enable_power_block_coupling: bool = True,
        enable_shadow_block_synergy: bool = True,
        enable_machine_exclusivity: bool = True,
        enable_job_precedence: bool = True,
        enable_headway_margins: bool = True,
        headway_margin_minutes: Optional[int] = None,
        max_allowed_train_delay_min: Optional[int] = None,
        shadow_block_bonus_weight: Optional[int] = None,
        department_compatibility: Optional[Dict[str, List[str]]] = None
    ):
        self.enable_power_block_coupling = enable_power_block_coupling
        self.enable_shadow_block_synergy = enable_shadow_block_synergy
        self.enable_machine_exclusivity = enable_machine_exclusivity
        self.enable_job_precedence = enable_job_precedence
        self.enable_headway_margins = enable_headway_margins
        
        # Load from configuration layer or parameter override
        self.headway_margin_minutes = (
            headway_margin_minutes if headway_margin_minutes is not None
            else rules_loader.get_value("safety_and_headway", "block_release_headway_buffer", 3)
        )
        self.max_allowed_train_delay_min = (
            max_allowed_train_delay_min if max_allowed_train_delay_min is not None
            else rules_loader.get_value("train_regulation", "max_mail_express_delay", 45)
        )
        self.shadow_block_bonus_weight = (
            shadow_block_bonus_weight if shadow_block_bonus_weight is not None
            else rules_loader.get_value("optimization_weights", "shadow_block_bonus", 4000)
        )
        self.dept_compatibility = (
            department_compatibility if department_compatibility is not None
            else rules_loader.get_value("department_compatibility", "shadow_block_co_location", {
                "ENG": ["TRD", "S_T", "MECH"],
                "TRD": ["ENG", "S_T", "MECH"],
                "S_T": ["ENG", "TRD", "MECH"],
                "MECH": ["ENG", "TRD", "S_T"]
            })
        )

        # Section order & bypass configurations
        self.section_order = rules_loader.get_value("corridor_sections", "section_order", [
            "NDLS-TKD", "TKD-FDB", "FDB-PWL", "PWL-KDS", "KDS-MTJ", "MTJ-AGC"
        ])
        self.third_line_sections = rules_loader.get_value("corridor_sections", "third_line_bypass_available", [
            "TKD-FDB", "FDB-PWL"
        ])

        # Delay limits by priority tier
        self.max_premium_delay = rules_loader.get_value("train_regulation", "max_premium_passenger_delay", 25)
        self.max_mail_delay = rules_loader.get_value("train_regulation", "max_mail_express_delay", 45)
        self.max_freight_holding = rules_loader.get_value("train_regulation", "max_freight_holding_time", 240)

        # Objective weights
        self.job_priority_multiplier = rules_loader.get_value("optimization_weights", "job_priority_multiplier", 2000)
        self.urgency_critical_bonus = rules_loader.get_value("optimization_weights", "urgency_bonus_critical", 3000)
        self.urgency_high_bonus = rules_loader.get_value("optimization_weights", "urgency_bonus_high", 1500)
        self.urgency_routine_bonus = rules_loader.get_value("optimization_weights", "urgency_bonus_routine", 800)

        self.penalty_premium_delay = rules_loader.get_value("optimization_weights", "penalty_premium_passenger_delay", 50)
        self.penalty_mail_delay = rules_loader.get_value("optimization_weights", "penalty_mail_express_delay", 20)
        self.penalty_freight_delay = rules_loader.get_value("optimization_weights", "penalty_freight_delay", 2)

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
