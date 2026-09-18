import time
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import httpx
from ..config import settings

# ---------------------------------------------------------------------------
# Corridor geography (Delhi - Agra Mainline, matches the 6 seeded sections)
# ---------------------------------------------------------------------------
_STATION_CODES = ["NDLS", "TKD", "FDB", "PWL", "KDS", "MTJ", "AGC"]
_STATION_FULL = {
    "NDLS": "New Delhi (NDLS)", "TKD": "Tuglakabad (TKD)", "FDB": "Faridabad (FDB)",
    "PWL": "Palwal (PWL)", "KDS": "Kosi Kalan (KDS)", "MTJ": "Mathura Jn (MTJ)",
    "AGC": "Agra Cantt (AGC)",
}
_CUM_KM = [0.0, 15.5, 29.7, 61.7, 103.7, 148.2, 202.0]
_IST_TZ = timezone(timedelta(hours=5, minutes=30))  # fixed IST offset (no tzdb dependency)

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
    status: str  # "ON_TIME", "DELAYED", "REGULATED"
    direction: str  # "UP", "DN"
    priority_weight: int
    source: str
    last_updated: str
    phase: str = ""
    progress_pct: float = 0.0
    progress_km: float = 0.0
    km_total: float = 0.0
    km_remaining: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def min_to_str(m: int) -> str:
    h = (m // 60) % 24
    mins = m % 60
    return f"{h:02d}:{mins:02d}"

def _ist_now() -> datetime:
    return datetime.now(_IST_TZ)

class BaseTrainDataProvider:
    def get_live_train_movements(self) -> List[NormalizedTrainMovement]:
        raise NotImplementedError

    def get_train_status(self, train_id: str) -> Optional[NormalizedTrainMovement]:
        raise NotImplementedError

    def get_station_board(self, station_id: str) -> List[NormalizedTrainMovement]:
        raise NotImplementedError


class MockTrainDataProvider(BaseTrainDataProvider):
    """
    Clock-driven "live" corridor replay provider.

    Positions, ETAs and delays are computed deterministically from the corridor
    timetable against the wall clock (IST), so trains visibly MOVE between
    refreshes exactly like a real live feed would -- while remaining honest
    synthetic demo data. A real live provider can later replace this class
    through the same adapter interface (see LiveTrainDataProvider).
    """

    # (id, name, type, direction, corridor-entry idx, corridor-exit idx,
    #  dep minute, arr minute, base delay, priority weight)
    TIMETABLE = [
        ("22436", "Vande Bharat Express", "VANDE_BHARAT", "DN", 0, 6, 360, 460, 0, 35),
        ("12050", "Gatimaan Express", "VANDE_BHARAT", "DN", 0, 6, 490, 590, 0, 35),
        ("12002", "Bhopal Shatabdi Express", "RAJDHANI", "DN", 0, 6, 375, 475, 0, 30),
        ("12952", "Mumbai Tejas Rajdhani", "RAJDHANI", "DN", 0, 6, 1015, 1115, 0, 35),
        ("12951", "Mumbai Rajdhani (Return)", "RAJDHANI", "UP", 6, 0, 480, 580, 0, 35),
        ("12301", "Howrah Rajdhani Express", "RAJDHANI", "DN", 0, 6, 1305, 1435, 0, 35),
        ("12302", "Howrah Rajdhani Express (Return)", "RAJDHANI", "UP", 6, 0, 1300, 1430, 0, 35),
        ("12626", "Kerala Express", "EXPRESS", "DN", 0, 6, 1210, 1330, 0, 20),
        ("12625", "Kerala Express (UP)", "EXPRESS", "UP", 6, 0, 780, 900, 0, 20),
        ("12622", "Tamil Nadu Express", "EXPRESS", "DN", 0, 6, 1235, 1375, 5, 20),
        ("12650", "Karnataka Sampark Kranti Express", "EXPRESS", "DN", 0, 6, 1120, 1250, 0, 20),
        ("12627", "Karnataka Express", "EXPRESS", "UP", 6, 0, 1010, 1140, 0, 20),
        ("12138", "Punjab Mail", "EXPRESS", "DN", 0, 6, 315, 435, 12, 15),
        ("12137", "Punjab Mail (UP)", "EXPRESS", "UP", 6, 0, 555, 685, 0, 15),
        ("12414", "Pooja Superfast Express", "EXPRESS", "UP", 6, 0, 230, 340, 5, 15),
        ("11058", "Amritsar Express", "EXPRESS", "DN", 0, 6, 690, 830, 0, 12),
        ("12780", "Goa Express", "EXPRESS", "DN", 0, 6, 900, 1020, 0, 15),
        ("12904", "Golden Temple Mail", "EXPRESS", "DN", 0, 6, 700, 830, 0, 15),
        ("14212", "Intercity Express", "PASSENGER", "DN", 0, 6, 1060, 1200, 0, 10),
        ("14211", "Intercity Express (UP)", "PASSENGER", "UP", 6, 0, 360, 500, 0, 10),
        ("04408", "Palwal-Delhi EMU Special", "PASSENGER", "UP", 3, 0, 450, 540, 0, 10),
        ("CONRAJ-01", "Container Cargo Special", "FREIGHT", "DN", 1, 6, 90, 210, 45, 5),
        ("CONRAJ-02", "Container Cargo Special (Night)", "FREIGHT", "DN", 1, 6, 1210, 1350, 20, 5),
        ("BOXN-12", "Thermal Coal Freight Rake", "FREIGHT", "DN", 1, 6, 620, 780, 0, 5),
        ("BOXN-14", "Thermal Coal Freight Rake (2)", "FREIGHT", "DN", 1, 6, 1150, 1300, 15, 5),
        ("BOXN-16", "Thermal Coal Freight Rake (3)", "FREIGHT", "DN", 1, 6, 210, 330, 0, 5),
        ("BTPN-04", "IOCL Petroleum Tanker Rake", "FREIGHT", "UP", 5, 1, 150, 270, 35, 5),
        ("BTPN-06", "IOCL Petroleum Tanker Rake (Night)", "FREIGHT", "UP", 5, 1, 1200, 1320, 10, 5),
        ("BOXN-18", "Thermal Coal Freight Rake (4)", "FREIGHT", "DN", 1, 6, 1335, 1435, 0, 5),
        ("CONRAJ-03", "Container Cargo Special (Late Night)", "FREIGHT", "DN", 1, 6, 1360, 1439, 15, 5),
    ]

    def __init__(self):
        self.simulated_delays: Dict[str, int] = {}

    def set_simulated_delay(self, train_id: str, delay_min: int):
        self.simulated_delays[train_id] = delay_min

    @staticmethod
    def _live_delay(base_delay: int, seed: int, now_dt: datetime) -> int:
        """Deterministic drift for already-late trains (on-time trains stay on time)."""
        if base_delay <= 0:
            return 0
        sec = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
        wob = 2.0 * math.sin((sec + seed * 97.0) / 61.0) + 1.5 * math.cos((sec + seed * 149.0) / 97.0)
        return max(1, int(base_delay + round(wob)))

    def _build_movement(self, t, now_dt: datetime, delay_override: Optional[int], seed: int = 0) -> NormalizedTrainMovement:
        tid, name, ttype, direction, entry, exit_i, dep, arr, base, prio = t
        delay = delay_override if delay_override is not None else self._live_delay(base, seed, now_dt)
        est_dep = dep + delay
        est_arr = arr + delay
        status = "ON_TIME" if delay == 0 else ("REGULATED" if ttype == "FREIGHT" else "DELAYED")

        now_float = now_dt.hour * 60 + now_dt.minute + now_dt.second / 60.0
        now_sec_str = now_dt.strftime("%H:%M:%S IST")

        lo, hi = min(entry, exit_i), max(entry, exit_i)
        dist_km = _CUM_KM[hi] - _CUM_KM[lo]
        runtime = max(1, arr - dep)
        f = max(0.0, min(1.0, (now_float - est_dep) / runtime))
        coord = _CUM_KM[entry] + (f * dist_km if direction == "DN" else -f * dist_km)

        if now_float < est_dep:
            phase = "PRE_DEP" if (est_dep - now_float) <= 75 else "IDLE"
        elif f < 1.0:
            phase = "RUNNING"
        elif (now_float - est_arr) <= 25:
            phase = "ARRIVED"
        else:
            phase = "IDLE"

        seg = None
        for i in range(lo, hi):
            if (_CUM_KM[i] <= coord < _CUM_KM[i + 1]) or (f >= 1.0 and i == hi - 1):
                seg = i
                break
        if seg is None:
            seg = lo if phase in ("PRE_DEP", "IDLE") else max(lo, hi - 1)


        if phase == "RUNNING":
            if f >= 1.0:
                phase = "ARRIVED"
                loc = "Arrived {} - cleared corridor at {}".format(_STATION_FULL[_STATION_CODES[exit_i]], min_to_str(est_arr))
                nxt = _STATION_FULL[_STATION_CODES[exit_i]]
            else:
                nxt_idx = seg + 1 if direction == "DN" else seg
                nxt_idx = max(0, min(6, nxt_idx))
                loc = "Between {} & {} - KM {:.1f}".format(
                    _STATION_FULL[_STATION_CODES[seg]],
                    _STATION_FULL[_STATION_CODES[seg + 1]],
                    coord,
                )
                nxt = _STATION_FULL[_STATION_CODES[nxt_idx]]
        elif phase == "PRE_DEP":
            nxt_idx = (entry + 1) if direction == "DN" else (entry - 1)
            nxt_idx = max(0, min(6, nxt_idx))
            loc = "Ready at {} platform - scheduled dep {}".format(_STATION_FULL[_STATION_CODES[entry]], min_to_str(est_dep))
            nxt = _STATION_FULL[_STATION_CODES[nxt_idx]]
        elif phase == "ARRIVED":
            loc = "Arrived {} - cleared corridor at {}".format(_STATION_FULL[_STATION_CODES[exit_i]], min_to_str(est_arr))
            nxt = _STATION_FULL[_STATION_CODES[exit_i]]
        else:
            loc = "Not in current corridor window - next run {}".format(min_to_str(est_dep))
            nxt = _STATION_FULL[_STATION_CODES[entry if direction == "DN" else exit_i]]

        section_code = "{}-{}".format(_STATION_CODES[seg], _STATION_CODES[seg + 1])
        track_line = "{}_DN".format(section_code) if direction == "DN" else "{}_UP".format(section_code)
        progress_km = round(f * dist_km, 1)

        return NormalizedTrainMovement(
            train_id=tid,
            train_name=name,
            train_type=ttype,
            section=section_code,
            track_line=track_line,
            current_location=loc,
            next_location=nxt,
            scheduled_departure_min=dep,
            scheduled_arrival_min=arr,
            estimated_departure_min=est_dep,
            estimated_arrival_min=est_arr,
            scheduled_departure_str=min_to_str(dep),
            scheduled_arrival_str=min_to_str(arr),
            estimated_departure_str=min_to_str(est_dep),
            estimated_arrival_str=min_to_str(est_arr),
            delay_minutes=delay,
            status=status,
            direction=direction,
            priority_weight=prio,
            source="Synthetic Demo Data",
            last_updated=now_sec_str,
            phase=phase,
            progress_pct=round(f * 100.0, 1),
            progress_km=progress_km,
            km_total=round(dist_km, 1),
            km_remaining=round(max(0.0, dist_km - progress_km), 1),
        )

    def get_live_train_movements(self) -> List[NormalizedTrainMovement]:
        now_dt = _ist_now()
        results = []
        for seed, t in enumerate(self.TIMETABLE):
            override = self.simulated_delays.get(t[0])
            results.append(self._build_movement(t, now_dt, override, seed))
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
    Connects to an external live / public train-running API (optional).
    Normalizes arbitrary external responses into NormalizedTrainMovement.
    """

    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or settings.LIVE_TRAIN_API_URL
        self.api_key = api_key or settings.LIVE_TRAIN_API_KEY
        self.client = httpx.Client(timeout=4.0)

    def get_live_train_movements(self) -> List[NormalizedTrainMovement]:
        if not self.api_key or not self.api_url:
            raise ConnectionError("Live Train API Key or URL not configured.")

        # Vendor endpoint - normalized below; any error triggers demo fallback.
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
            phase = str(item.get("phase", "RUNNING"))
            f_prog = float(item.get("progress_pct", 0.0))

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
                last_updated=now_str,
                phase=phase,
                progress_pct=f_prog,
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
    Adapter orchestrating live provider, replay provider, caching, and automatic fallback.
    Ensures zero failure for demo under network outages.
    """

    def __init__(self):
        self.mock_provider = MockTrainDataProvider()
        self.live_provider = LiveTrainDataProvider()
        self.cache_ttl = settings.TRAIN_CACHE_TTL_SECONDS
        self._cached_movements: Optional[List[NormalizedTrainMovement]] = None
        self._last_cache_time = 0.0
        self._active_provider_label = "Synthetic Demo Data"

    def _payload(self, movements: List[NormalizedTrainMovement], cache_age: float) -> Dict[str, Any]:
        active = [m for m in movements if m.phase in ("RUNNING", "PRE_DEP", "ARRIVED")]
        return {
            "source": self._active_provider_label,
            "is_fallback": "Synthetic" in self._active_provider_label,
            "mode": "timetable_replay" if "Synthetic" in self._active_provider_label else "live",
            "is_simulated": "Synthetic" in self._active_provider_label,
            "timezone": "Asia/Kolkata",
            "as_of": datetime.now(_IST_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "active_count": len(active),
            "cache_age_seconds": round(cache_age, 1),
            "movements": [m.to_dict() for m in movements],
        }

    def get_movements(self, force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()

        if not force_refresh and self._cached_movements and (now - self._last_cache_time < self.cache_ttl):
            return self._payload(self._cached_movements, now - self._last_cache_time)

        movements = None
        provider_mode = settings.TRAIN_DATA_PROVIDER.lower()

        if provider_mode in ("auto", "live") and settings.LIVE_TRAIN_API_KEY:
            try:
                movements = self.live_provider.get_live_train_movements()
                self._active_provider_label = "Live/Public Train Data"
            except Exception:
                movements = self.mock_provider.get_live_train_movements()
                self._active_provider_label = "Synthetic Demo Data (Fallback)"
        else:
            movements = self.mock_provider.get_live_train_movements()
            self._active_provider_label = "Synthetic Demo Data"

        self._cached_movements = movements
        self._last_cache_time = now
        return self._payload(movements, 0.0)

    def simulate_delay(self, train_id: str, delay_minutes: int) -> Dict[str, Any]:
        self.mock_provider.set_simulated_delay(train_id, delay_minutes)
        self._cached_movements = None
        return self.get_movements(force_refresh=True)


train_adapter = TrainDataAdapter()
