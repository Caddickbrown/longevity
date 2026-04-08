from datetime import datetime
from unittest.mock import patch

import pytest

from backend.services.health_bridge import (
    HealthBridgeError,
    parse_readings,
    fetch_health_data,
)

SAMPLE_DATA = {
    "steps":      [{"date": "2026-04-07", "value": 8500.0}],
    "resting_hr": [{"date": "2026-04-07", "value": 58.0}],
    "heart_rate": [{"date": "2026-04-07", "min": 52.0, "avg": 74.0, "max": 110.0}],
    "sleep": [{"date": "2026-04-07", "Deep": 90.0, "REM": 60.0, "Core": 240.0, "Awake": 30.0}],
    "weight":   [{"date": "2026-04-07", "value": 78.5}],
    "body_fat": [{"date": "2026-04-07", "value": 18.2}],
    "active_energy": [],
    "basal_energy": [],
    "distance": [],
    "flights": [],
    "walking_speed": [],
    "bmi": [],
    "dietary_protein": [],
    "dietary_carbs": [],
    "dietary_fat_total": [],
    "dietary_fiber": [],
    "vo2_max": [],
    "hrv": [],
}


def test_parse_readings_simple_metrics():
    readings = parse_readings(SAMPLE_DATA)
    metrics = {r["metric"] for r in readings}
    assert "steps" in metrics
    assert "resting_hr" in metrics
    assert "weight_kg" in metrics
    assert "body_fat_pct" in metrics


def test_parse_readings_heart_rate_splits_into_three():
    readings = parse_readings(SAMPLE_DATA)
    metrics = {r["metric"] for r in readings}
    assert "hr_min" in metrics
    assert "hr_avg" in metrics
    assert "hr_max" in metrics


def test_parse_readings_sleep_stages():
    readings = parse_readings(SAMPLE_DATA)
    metrics = {r["metric"] for r in readings}
    assert "sleep_deep_mins" in metrics
    assert "sleep_rem_mins" in metrics
    assert "sleep_core_mins" in metrics
    assert "sleep_awake_mins" in metrics
    assert "sleep_total_mins" in metrics


def test_parse_readings_sleep_total_calculation():
    readings = parse_readings(SAMPLE_DATA)
    total = next(r for r in readings if r["metric"] == "sleep_total_mins")
    # Deep 90 + REM 60 + Core 240 = 390 (Awake excluded from total)
    assert total["value"] == 390.0


def test_parse_readings_skips_none_values():
    data = {**SAMPLE_DATA, "weight": [{"date": "2026-04-07", "value": None}]}
    readings = parse_readings(data)
    metrics = {r["metric"] for r in readings}
    assert "weight_kg" not in metrics


def test_parse_readings_source_is_health_at_home():
    readings = parse_readings(SAMPLE_DATA)
    assert all(r["source"] == "health_at_home" for r in readings)


def test_parse_readings_recorded_at_is_datetime():
    readings = parse_readings(SAMPLE_DATA)
    assert all(isinstance(r["recorded_at"], datetime) for r in readings)


def test_fetch_health_data_raises_on_connection_error():
    import httpx as _httpx
    with patch("httpx.get", side_effect=_httpx.RequestError("connection refused")):
        with pytest.raises(HealthBridgeError):
            fetch_health_data(7)
