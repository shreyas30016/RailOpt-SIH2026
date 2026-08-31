import os
from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "railway_rules.yaml"

class RailwayRulesLoader:
    """
    Loads and exposes structured railway domain rules from backend/config/railway_rules.yaml.
    Guarantees that no unvalidated operational rules or magic numbers are hardcoded inside solver algorithms.
    """
    _instance = None
    _rules_cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RailwayRulesLoader, cls).__new__(cls)
            cls._instance._load_rules()
        return cls._instance

    def _load_rules(self):
        if HAS_YAML and CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self._rules_cache = yaml.safe_load(f) or {}
                return
            except Exception as e:
                print(f"[!] Warning: Could not load YAML rules from {CONFIG_PATH}: {e}")

        # In-code fallback if YAML is missing or cannot be read
        self._rules_cache = {
            "safety_and_headway": {
                "block_release_headway_buffer": {"value": 3, "status": "PROTOTYPE_ASSUMPTION"},
                "power_isolation_permit_margin": {"value": 10, "status": "PROTOTYPE_ASSUMPTION"},
                "caution_order_clearing_speed": {"value": 30, "status": "VALIDATED"}
            },
            "department_compatibility": {
                "shadow_block_co_location": {
                    "value": {
                        "ENG": ["TRD", "S_T", "MECH"],
                        "TRD": ["ENG", "S_T", "MECH"],
                        "S_T": ["ENG", "TRD", "MECH"],
                        "MECH": ["ENG", "TRD", "S_T"]
                    },
                    "status": "PROTOTYPE_ASSUMPTION"
                }
            },
            "corridor_sections": {
                "section_order": {
                    "value": ["NDLS-TKD", "TKD-FDB", "FDB-PWL", "PWL-KDS", "KDS-MTJ", "MTJ-AGC"],
                    "status": "VALIDATED"
                },
                "third_line_bypass_available": {
                    "value": ["TKD-FDB", "FDB-PWL"],
                    "status": "VALIDATED"
                }
            },
            "train_regulation": {
                "max_freight_holding_time": {"value": 240, "status": "PROTOTYPE_ASSUMPTION"},
                "max_mail_express_delay": {"value": 45, "status": "VALIDATED"},
                "max_premium_passenger_delay": {"value": 25, "status": "VALIDATED"}
            },
            "optimization_weights": {
                "job_priority_multiplier": {"value": 2000, "status": "PROTOTYPE_ASSUMPTION"},
                "urgency_bonus_critical": {"value": 3000, "status": "PROTOTYPE_ASSUMPTION"},
                "urgency_bonus_high": {"value": 1500, "status": "PROTOTYPE_ASSUMPTION"},
                "urgency_bonus_routine": {"value": 800, "status": "PROTOTYPE_ASSUMPTION"},
                "shadow_block_bonus": {"value": 4000, "status": "PROTOTYPE_ASSUMPTION"},
                "penalty_premium_passenger_delay": {"value": 50, "status": "PROTOTYPE_ASSUMPTION"},
                "penalty_mail_express_delay": {"value": 20, "status": "PROTOTYPE_ASSUMPTION"},
                "penalty_freight_delay": {"value": 2, "status": "PROTOTYPE_ASSUMPTION"}
            }
        }

    def get_rule_entry(self, category: str, rule_key: str) -> Dict[str, Any]:
        return self._rules_cache.get(category, {}).get(rule_key, {})

    def get_value(self, category: str, rule_key: str, default: Any = None) -> Any:
        entry = self.get_rule_entry(category, rule_key)
        if isinstance(entry, dict) and "value" in entry:
            return entry["value"]
        return default if default is not None else entry

    @property
    def raw_rules(self) -> Dict[str, Any]:
        return self._rules_cache

rules_loader = RailwayRulesLoader()
