from datetime import date, datetime
from typing import Any

from garminconnect import Garmin

from backend.config import settings


class GarminSyncError(Exception):
    pass


def get_garmin_client() -> Garmin:
    if not settings.garmin_email or not settings.garmin_password:
        raise GarminSyncError("GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
    client = Garmin(email=settings.garmin_email, password=settings.garmin_password)
    client.login()
    return client


def _safe_get(data: dict | None, *keys: str) -> Any:
    """Safely traverse nested dict keys, returning None if any key is missing."""
    if data is None:
        return None
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
        if data is None:
            return None
    return data


def extract_metrics(api: Any, for_date: date) -> list[dict]:
    """
    Extract all available biomarker metrics from Garmin API for a given date.
    Returns list of dicts ready to create BiomarkerReading records.
    Skips any metric where the API returns None.
    """
    date_str = for_date.isoformat()
    recorded_at = datetime.combine(for_date, datetime.min.time())
    readings = []

    def add(metric: str, value: Any, unit: str) -> None:
        if value is not None:
            readings.append({
                "source": "garmin",
                "metric": metric,
                "value": float(value),
                "unit": unit,
                "recorded_at": recorded_at,
            })

    # Daily stats
    stats = api.get_stats(date_str)
    add("steps", _safe_get(stats, "totalSteps"), "count")
    add("resting_hr", _safe_get(stats, "restingHeartRate"), "bpm")
    add("stress", _safe_get(stats, "averageStressLevel"), "score")
    add("body_battery", _safe_get(stats, "bodyBatteryChargedValue"), "score")

    # Sleep
    sleep = api.get_sleep_data(date_str)
    sleep_dto = _safe_get(sleep, "dailySleepDTO")
    add("sleep_score", _safe_get(sleep_dto, "sleepScore"), "score")
    add("deep_sleep_seconds", _safe_get(sleep_dto, "deepSleepSeconds"), "seconds")
    add("light_sleep_seconds", _safe_get(sleep_dto, "lightSleepSeconds"), "seconds")
    add("rem_sleep_seconds", _safe_get(sleep_dto, "remSleepSeconds"), "seconds")

    # HRV
    hrv = api.get_hrv_data(date_str)
    add("hrv_last_night", _safe_get(hrv, "hrvSummary", "lastNight"), "ms")

    # Body composition
    body = api.get_body_composition(date_str)
    body_avg = _safe_get(body, "totalAverage")
    add("weight_kg", _safe_get(body_avg, "weight"), "kg")
    add("body_fat_pct", _safe_get(body_avg, "bodyFatPercentage"), "%")

    return readings


def sync_date(api: Any, for_date: date, db_session: Any) -> int:
    """
    Sync one day of Garmin data into the database.
    Skips metrics that already exist for that date.
    Returns count of new readings inserted.
    """
    from sqlalchemy import select
    from backend.models import BiomarkerReading

    metrics = extract_metrics(api, for_date)
    date_str = for_date.isoformat()

    existing = set(
        db_session.execute(
            select(BiomarkerReading.metric).where(
                BiomarkerReading.source == "garmin",
                BiomarkerReading.recorded_at >= datetime.fromisoformat(date_str),
                BiomarkerReading.recorded_at < datetime.fromisoformat(date_str + "T23:59:59"),
            )
        ).scalars().all()
    )

    inserted = 0
    for reading in metrics:
        if reading["metric"] not in existing:
            db_session.add(BiomarkerReading(**reading))
            inserted += 1

    db_session.commit()
    return inserted
