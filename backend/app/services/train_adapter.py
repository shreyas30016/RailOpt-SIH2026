import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import httpx
from ..config import settings

@dataclass
class NormalizedTrainMovement:
    train_id: str
    train_name: str
    train_type: str
    section: str
    track_line: str
    current_location: str
    next_location: str
    scheduled_departure_min: int
    scheduled_arrival_min: int
    estimated_departure_min: int
    estimated_arrival_min: int
    scheduled_departure_str: str
    scheduled_arrival_str: str
    estimated_departure_str: str
    estimated_arrival_str: str
    delay_minutes: int
    status: str # "ON_TIME", "DELAYED", "REGULATED"
    direction: str # "UP", "DN"
    priority_weight: int
    source: str # "Live/Public Train Data" or "Synthetic Demo Data"
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def min_to_str(m: int) -> str:
    h = (m // 60) % 24
    mins = m % 60
    return f"{h:02d}:{mins:02d}"

class BaseTrainDataProvider:
    def get_live_train_movements(self) -> List[NormalizedTrainMovement]:
        raise NotImplementedError

    def get_train_status(self, train_id: str) -> Optional[NormalizedTrainMovement]:
        raise NotImplementedError

    def get_station_board(self, station_id: str) -> List[NormalizedTrainMovement]:
        raise NotImplementedError

class MockTrainDataProvider(BaseTrainDataProvider):
    """
    High-fidelity realistic Indian Railways corridor mock provider (Delhi-Agra Mainline).
    Acts as provider or zero-latency fallback when external live APIs are unavailable.
    """
    def __init__(self):
        self.simulated_delays: Dict[str, int] = {}

    def set_simulated_delay(self, train_id: str, delay_min: int):
        self.simulated_delays[train_id] = delay_min

    def get_live_train_movements(self) -> List[NormalizedTrainMovement]:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        base_trains = [
            {
                "train_id": "22436",
                "train_name": "Vande Bharat Express",
                "train_type": "VANDE_BHARAT",
                "section": "NDLS-TKD",
                "track_line": "NDLS-TKD_DN",
                "current_location": "Approaching Tuglakabad (TKD)",
                "next_location": "Faridabad (FDB)",
                "dep_min": 360, # 06:00
                "arr_min": 460, # 07:40
                "direction": "DN",
                "priority_weight": 35,
                "default_delay": 0
            },
            {
                "train_id": "12050",
                "train_name": "Gatimaan Express",
                "train_type": "VANDE_BHARAT",
                "section": "TKD-FDB",
                "track_line": "TKD-FDB_DN",
                "current_location": "Passing Faridabad Outer",
                "next_location": "Palwal (PWL)",
                "dep_min": 490, # 08:10
                "arr_min": 590, # 09:50
                "direction": "DN",
                "priority_weight": 35,
                "default_delay": 0
            },
            {
                "train_id": "12952",
                "train_name": "Mumbai Tejas Rajdhani",
                "train_type": "RAJDHANI",
                "section": "FDB-PWL",
                "track_line": "FDB-PWL_DN",
                "current_location": "Departed New Delhi Platform 4",
                "next_location": "Mathura Jn (MTJ)",
                "dep_min": 1015, # 16:55
                "arr_min": 1115, # 18:35
                "direction": "DN",
                "priority_weight": 35,
                "default_delay": 0
            },
            {
                "train_id": "12138",
                "train_name": "Punjab Mail",
                "train_type": "EXPRESS",
                "section": "PWL-KDS",
                "track_line": "PWL-KDS_DN",
                "current_location": "Crossing Palwal Junction",
                "next_location": "Kosi Kalan (KDS)",
                "dep_min": 315, # 05:15
                "arr_min": 435, # 07:15
                "direction": "DN",
                "priority_weight": 15,
                "default_delay": 12
            },
            {
                "train_id": "12414",
                "train_name": "Pooja Superfast Express",
                "train_type": "EXPRESS",
                "section": "KDS-MTJ",
                "track_line": "KDS-MTJ_UP",
                "current_location": "Approaching Kosi Kalan",
                "next_location": "Palwal (PWL)",
                "dep_min": 230, # 03:50
                "arr_min": 340, # 05:40
                "direction": "UP",
                "priority_weight": 15,
                "default_delay": 5
            },
            {
                "train_id": "CONRAJ-01",
                "train_name": "Container Cargo Special",
                "train_type": "FREIGHT",
                "section": "FDB-PWL",
                "track_line": "FDB-PWL_3RD",
                "current_location": "Regulated at Tuglakabad Yard Siding",
                "next_location": "Palwal Yard (PWL)",
                "dep_min": 90, # 01:30
                "arr_min": 210, # 03:30
                "direction": "DN",
                "priority_weight": 5,
                "default_delay": 45
            },
            {
                "train_id": "BTPN-04",
                "train_name": "IOCL Petroleum Tanker Rake",
                "train_type": "FREIGHT",
                "section": "MTJ-AGC",
                "track_line": "MTJ-AGC_UP",
                "current_location": "Mathura Refinery Loop",
                "next_location": "Tuglakabad (TKD)",
                "dep_min": 150, # 02:30
                "arr_min": 270, # 04:30
                "direction": "UP",
                "priority_weight": 5,
                "default_delay": 35
            }
        ]

        results = []
        for t in base_trains:
            tid = t["train_id"]
            # Apply dynamic or simulated delay override if present
            delay = self.simulated_delays.get(tid, t["default_delay"])
            status = "ON_TIME" if delay == 0 else ("REGULATED" if t["train_type"] == "FREIGHT" else "DELAYED")
            
            est_dep = t["dep_min"] + delay
            est_arr = t["arr_min"] + delay

            results.append(NormalizedTrainMovement(
                train_id=tid,
                train_name=t["train_name"],
                train_type=t["train_type"],
                section=t["section"],
                track_line=t["track_line"],
                current_location=t["current_location"],
                next_location=t["next_location"],
                scheduled_departure_min=t["dep_min"],
                scheduled_arrival_min=t["arr_min"],
                estimated_departure_min=est_dep,
                estimated_arrival_min=est_arr,
                scheduled_departure_str=min_to_str(t["dep_min"]),
                scheduled_arrival_str=min_to_str(t["arr_min"]),
                estimated_departure_str=min_to_str(est_dep),
                estimated_arrival_str=min_to_str(est_arr),
                delay_minutes=delay,
                status=status,
                direction=t["direction"],
                priority_weight=t["priority_weight"],
                source="Synthetic Demo Data",
                last_updated=now_str
            ))
        return results

    def get_train_status(self, train_id: str) -> Optional[NormalizedTrainMovement]:
        movements = self.get_live_train_movements()
        for m in movements:
            if m.train_id == train_id:
                return m
        return None

    def get_station_board(self, station_id: str) -> List[NormalizedTrainMovement]:
        movements = self.get_live_train_movements()
        return [m for m in movements if station_id in m.section or station_id in m.current_location or station_id in m.next_location]

class LiveTrainDataProvider(BaseTrainDataProvider):
    """
    Connects to external live / public train-running APIs (e.g. public Indian Railways feed).
    Normalizes arbitrary external responses into NormalizedTrainMovement.
    """
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or settings.LIVE_TRAIN_API_URL
        self.api_key = api_key or settings.LIVE_TRAIN_API_KEY
        self.client = httpx.Client(timeout=4.0)

    def get_live_train_movements(self) -> List[NormalizedTrainMovement]:
        if not self.api_key or not self.api_url:
            raise ConnectionError("Live Train API Key or URL not configured.")
        
        # Example external call (protected by try/catch with strict timeout)
        resp = self.client.get(f"{self.api_url}live-corridor?corridor=NDLS-AGC&apikey={self.api_key}")
        if resp.status_code != 200:
            raise ConnectionError(f"Live Train API returned status code {resp.status_code}")
        
        data = resp.json()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        normalized_list = []
        for item in data.get("trains", []):
            sched_dep = item.get("scheduled_departure_min", 360)
            sched_arr = item.get("scheduled_arrival_min", 480)
            delay = item.get("delay_minutes", 0)
            
            normalized_list.append(NormalizedTrainMovement(
                train_id=str(item.get("train_number")),
                train_name=item.get("train_name", "Express"),
                train_type=item.get("train_type", "EXPRESS"),
                section=item.get("section", "NDLS-TKD"),
                track_line=item.get("track_line", "UP_MAIN"),
                current_location=item.get("current_location", "En Route"),
                next_location=item.get("next_location", "Next Junction"),
                scheduled_departure_min=sched_dep,
                scheduled_arrival_min=sched_arr,
                estimated_departure_min=sched_dep + delay,
                estimated_arrival_min=sched_arr + delay,
                scheduled_departure_str=min_to_str(sched_dep),
                scheduled_arrival_str=min_to_str(sched_arr),
                estimated_departure_str=min_to_str(sched_dep + delay),
                estimated_arrival_str=min_to_str(sched_arr + delay),
                delay_minutes=delay,
                status="ON_TIME" if delay == 0 else "DELAYED",
                direction=item.get("direction", "DN"),
                priority_weight=item.get("priority_weight", 15),
                source="Live/Public Train Data",
                last_updated=now_str
            ))
        return normalized_list

    def get_train_status(self, train_id: str) -> Optional[NormalizedTrainMovement]:
        movements = self.get_live_train_movements()
        for m in movements:
            if m.train_id == train_id:
                return m
        return None

    def get_station_board(self, station_id: str) -> List[NormalizedTrainMovement]:
        movements = self.get_live_train_movements()
        return [m for m in movements if station_id in m.section or station_id in m.current_location]

class TrainDataAdapter:
    """
    Adapter orchestrating live provider, mock provider, caching, and automatic fallback.
    Ensures zero failure for demo under network outages.
    """
    def __init__(self):
        self.mock_provider = MockTrainDataProvider()
        self.live_provider = LiveTrainDataProvider()
        self.cache_ttl = settings.TRAIN_CACHE_TTL_SECONDS
        self._cached_movements: Optional[List[NormalizedTrainMovement]] = None
        self._last_cache_time = 0.0
        self._active_provider_label = "Synthetic Demo Data"

    def get_movements(self, force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()
        
        # Check cache
        if not force_refresh and self._cached_movements and (now - self._last_cache_time < self.cache_ttl):
            return {
                "source": self._active_provider_label,
                "is_fallback": self._active_provider_label == "Synthetic Demo Data",
                "cache_age_seconds": round(now - self._last_cache_time, 1),
                "movements": [m.to_dict() for m in self._cached_movements]
            }

        movements = None
        provider_mode = settings.TRAIN_DATA_PROVIDER.lower()

        # Attempt Live Provider if enabled
        if provider_mode in ("auto", "live") and settings.LIVE_TRAIN_API_KEY:
            try:
                movements = self.live_provider.get_live_train_movements()
                self._active_provider_label = "Live/Public Train Data"
            except Exception as e:
                # Automatic fallback on any network error or timeout
                movements = self.mock_provider.get_live_train_movements()
                self._active_provider_label = "Synthetic Demo Data (Fallback)"
        else:
            movements = self.mock_provider.get_live_train_movements()
            self._active_provider_label = "Synthetic Demo Data"

        self._cached_movements = movements
        self._last_cache_time = now

        return {
            "source": self._active_provider_label,
            "is_fallback": "Synthetic" in self._active_provider_label,
            "cache_age_seconds": 0.0,
            "movements": [m.to_dict() for m in movements]
        }

    def simulate_delay(self, train_id: str, delay_minutes: int) -> Dict[str, Any]:
        self.mock_provider.set_simulated_delay(train_id, delay_minutes)
        # Invalidate cache so changes take effect immediately
        self._cached_movements = None
        return self.get_movements(force_refresh=True)

train_adapter = TrainDataAdapter()
