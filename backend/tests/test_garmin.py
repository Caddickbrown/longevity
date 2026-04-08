from datetime import date
from unittest.mock import MagicMock

from backend.services.garmin import GarminSyncError, extract_metrics


def _mock_garmin_api():
    api = MagicMock()
    api.get_stats.return_value = {
        "totalSteps": 8500,
        "restingHeartRate": 58,
        "averageStressLevel": 32,
        "bodyBatteryChargedValue": 85,
    }
    api.get_sleep_data.return_value = {
        "dailySleepDTO": {
            "sleepScore": 76,
            "deepSleepSeconds": 5400,
            "lightSleepSeconds": 12600,
            "remSleepSeconds": 7200,
            "awakeSleepSeconds": 900,
        }
    }
    api.get_hrv_data.return_value = {
        "hrvSummary": {
            "lastNight": 52,
        }
    }
    api.get_body_composition.return_value = {
        "totalAverage": {
            "weight": 78.5,
            "bodyFatPercentage": 18.2,
        }
    }
    return api


def test_extract_metrics_returns_readings():
    api = _mock_garmin_api()
    readings = extract_metrics(api, date(2026, 4, 7))
    metrics = {r["metric"] for r in readings}
    assert "steps" in metrics
    assert "resting_hr" in metrics
    assert "sleep_score" in metrics
    assert "hrv_last_night" in metrics
    assert "weight_kg" in metrics
    assert "body_fat_pct" in metrics


def test_extract_metrics_skips_none_values():
    api = _mock_garmin_api()
    api.get_stats.return_value = {"totalSteps": None, "restingHeartRate": 58}
    api.get_sleep_data.return_value = {"dailySleepDTO": None}
    api.get_hrv_data.return_value = {"hrvSummary": None}
    api.get_body_composition.return_value = {"totalAverage": None}

    readings = extract_metrics(api, date(2026, 4, 7))
    metrics = {r["metric"] for r in readings}
    assert "steps" not in metrics
    assert "resting_hr" in metrics


def test_extract_metrics_correct_units():
    api = _mock_garmin_api()
    readings = extract_metrics(api, date(2026, 4, 7))
    hrv = next(r for r in readings if r["metric"] == "hrv_last_night")
    assert hrv["unit"] == "ms"
    weight = next(r for r in readings if r["metric"] == "weight_kg")
    assert weight["unit"] == "kg"
