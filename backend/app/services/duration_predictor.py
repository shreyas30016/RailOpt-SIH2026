from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseDurationPredictor(ABC):
    """
    Abstract contract for maintenance duration prediction (AGENTS.md §9).
    Decouples the optimization solver from specific ML/heuristic implementations.
    """

    @abstractmethod
    def predict(
        self,
        job_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict maintenance duration.

        Returns:
            {
                "predictedDuration": int (minutes),
                "lowerBound": int,
                "upperBound": int,
                "confidence": float (0.0 to 1.0),
                "modelStatus": str ("DETERMINISTIC_BASELINE" | "TRAINED_MODEL"),
                "reasoning": str
            }
        """
        pass


class DeterministicDurationPredictor(BaseDurationPredictor):
    """
    Deterministic baseline implementation using domain heuristics.
    Status: PROTOTYPE_ASSUMPTION (Pending domain validation with railway experts).
    """

    # Base duration heuristics per department (minutes) — PROTOTYPE_ASSUMPTION
    _BASE_DURATIONS: Dict[str, int] = {
        "ENG": 210,
        "TRD": 150,
        "S_T": 120,
        "MECH": 180,
    }

    # Urgency multipliers — PROTOTYPE_ASSUMPTION
    _URGENCY_MULTIPLIERS: Dict[str, float] = {
        "CRITICAL": 1.30,
        "HIGH": 1.15,
        "MEDIUM": 1.00,
        "ROUTINE": 0.90,
    }

    # Resource type speedup factors — PROTOTYPE_ASSUMPTION
    _RESOURCE_FACTORS: Dict[str, float] = {
        "MACHINE": 0.85,
        "CREW": 1.00,
        "TOWER_WAGON": 0.90,
    }

    # Length overhead per km past 15 km baseline — PROTOTYPE_ASSUMPTION
    _LENGTH_FACTOR_MIN_PER_KM: float = 2.0

    def predict(
        self,
        job_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        context = context or {}
        dept = job_data.get("department_code", "ENG")
        urgency = job_data.get("urgency", "MEDIUM")
        stated = job_data.get("duration_minutes", 0)
        res_type = job_data.get("resource_type", "CREW")
        sec_len = float(context.get("section_length_km", 15.0))
        weather = float(context.get("weather_factor", 1.0))

        base = float(stated) if stated and stated > 0 else float(self._BASE_DURATIONS.get(dept, 180))
        urg_m = self._URGENCY_MULTIPLIERS.get(urgency, 1.0)
        len_adj = max(0.0, (sec_len - 15.0)) * self._LENGTH_FACTOR_MIN_PER_KM
        res_m = self._RESOURCE_FACTORS.get(res_type, 1.0)
        pwr_overhead = 20 if job_data.get("requires_power_block", False) else 0

        pred = max(30, round((base * urg_m * res_m * weather) + len_adj + pwr_overhead))
        lower = max(30, round(pred * 0.80))
        upper = round(pred * 1.25)
        confidence = 0.55  # PROTOTYPE_ASSUMPTION — real ML model will calibrate confidence

        reasoning = (
            f"Deterministic baseline: dept={dept}, urgency={urgency}, "
            f"base={base:.0f}min, urg_mult={urg_m:.2f}, res_mult={res_m:.2f}, "
            f"weather={weather:.1f}, pwr_overhead={pwr_overhead}min, len_adj={len_adj:.0f}min."
        )

        return {
            "predictedDuration": pred,
            "lowerBound": lower,
            "upperBound": upper,
            "confidence": confidence,
            "modelStatus": "DETERMINISTIC_BASELINE",
            "reasoning": reasoning,
        }


class MLDurationPredictorStub(BaseDurationPredictor):
    """
    Future ML Model Integration Slot.
    Will load serialized model (XGBoost / LightGBM) trained on historical block logs.
    Currently raises NotImplementedError or redirects to baseline.
    """

    def predict(
        self,
        job_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "ML model not yet integrated. Use DeterministicDurationPredictor baseline."
        )


class DurationPredictionService:
    """
    Unified service facade.
    Permits switching between deterministic baseline and ML model transparently.
    """

    def __init__(self, predictor: Optional[BaseDurationPredictor] = None):
        self._predictor = predictor or DeterministicDurationPredictor()

    def set_predictor(self, predictor: BaseDurationPredictor) -> None:
        self._predictor = predictor

    def predict(
        self,
        job_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self._predictor.predict(job_data, context)


# Singleton exported service
duration_predictor = DurationPredictionService()

