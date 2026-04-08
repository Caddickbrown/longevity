import logging
from datetime import date, datetime, timedelta
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

HEALTH_AT_HOME_URL = settings.health_at_home_url

# Metrics with simple {date, value} structure → (our_metric_name, unit)
SIMPLE_METRICS: dict[str, tuple[str, str]] = {
    "steps":         ("steps", "count"),
    "active_energy": ("active_energy_kcal", "kcal"),
    "basal_energy":  ("basal_energy_kcal", "kcal"),
    "resting_hr":    ("resting_hr", "bpm"),
    "weight":        ("weight_kg", "kg"),
    "bmi":           ("bmi", ""),
    "body_fat":      ("body_fat_pct", "%"),
    "distance":      ("distance_km", "km"),
    "flights":       ("flights_climbed", "count"),
    "walking_speed": ("walking_speed_kmh", "km/h"),
    "dietary_protein":   ("dietary_protein_g", "g"),
    "dietary_carbs":     ("dietary_carbs_g", "g"),
    "dietary_fat_total": ("dietary_fat_g", "g"),
    "dietary_fiber":     ("dietary_fiber_g", "g"),
}


class HealthBridgeError(Exception):
    pass


def fetch_health_data(days: int) -> dict[str, list[dict]]:
    """Fetch data from health-at-home API. Raises HealthBridgeError on failure."""
    try:
        response = httpx.get(
            f"{HEALTH_AT_HOME_URL}/api/health",
            params={"days": days},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise HealthBridgeError(f"Cannot reach health-at-home at {HEALTH_AT_HOME_URL}: {e}")
    except httpx.HTTPStatusError as e:
        raise HealthBridgeError(f"health-at-home returned {e.response.status_code}")


def parse_readings(data: dict[str, list[dict]]) -> list[dict]:
    """
    Convert health-at-home API response to list of BiomarkerReading dicts.
    Each dict has: source, metric, value, unit, recorded_at (datetime).
    """
    readings: list[dict] = []

    def add(metric: str, value: Any, unit: str, day: str) -> None:
        if value is None:
            return
        try:
            recorded_at = datetime.fromisoformat(day)
        except ValueError:
            return
        readings.append({
            "source": "health_at_home",
            "metric": metric,
            "value": float(value),
            "unit": unit,
            "recorded_at": recorded_at,
        })

    # Simple {date, value} metrics
    for api_key, (metric_name, unit) in SIMPLE_METRICS.items():
        for row in data.get(api_key) or []:
            add(metric_name, row.get("value"), unit, row["date"])

    # Heart rate: {date, min, avg, max}
    for row in data.get("heart_rate") or []:
        add("hr_min",  row.get("min"), "bpm", row["date"])
        add("hr_avg",  row.get("avg"), "bpm", row["date"])
        add("hr_max",  row.get("max"), "bpm", row["date"])

    # Sleep: {date, Deep, REM, Core, Awake} — all in minutes
    for row in data.get("sleep") or []:
        add("sleep_deep_mins",  row.get("Deep"),  "min", row["date"])
        add("sleep_rem_mins",   row.get("REM"),   "min", row["date"])
        add("sleep_core_mins",  row.get("Core"),  "min", row["date"])
        add("sleep_awake_mins", row.get("Awake"), "min", row["date"])
        # Derived: total sleep duration
        total = sum(
            (row.get(s) or 0)
            for s in ("Deep", "REM", "Core")
        )
        if total > 0:
            add("sleep_total_mins", total, "min", row["date"])

    return readings


def sync_to_db(readings: list[dict], db_session: Any) -> int:
    """
    Insert new readings into the database, skipping duplicates.
    Returns count of inserted readings.
    """
    from sqlalchemy import select
    from backend.models import BiomarkerReading

    if not readings:
        return 0

    # Build set of (metric, date_str) already in DB for health_at_home source
    dates_in_batch = {r["recorded_at"].date().isoformat() for r in readings}
    existing = set()
    for day_str in dates_in_batch:
        rows = db_session.execute(
            select(BiomarkerReading.metric).where(
                BiomarkerReading.source == "health_at_home",
                BiomarkerReading.recorded_at >= datetime.fromisoformat(day_str),
                BiomarkerReading.recorded_at < datetime.fromisoformat(day_str + "T23:59:59"),
            )
        ).scalars().all()
        for metric in rows:
            existing.add((metric, day_str))

    inserted = 0
    for r in readings:
        key = (r["metric"], r["recorded_at"].date().isoformat())
        if key not in existing:
            db_session.add(BiomarkerReading(**r))
            inserted += 1

    db_session.commit()
    return inserted


def sync(days: int, db_session: Any) -> int:
    """
    Fetch `days` of health data and sync to database.
    Returns count of new readings inserted.
    """
    data = fetch_health_data(days)
    readings = parse_readings(data)
    return sync_to_db(readings, db_session)
