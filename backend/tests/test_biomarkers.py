from datetime import datetime

from backend.models import BiomarkerReading
from backend.database import Base


def test_biomarker_table_exists(db):
    tables = Base.metadata.tables.keys()
    assert "biomarker_readings" in tables


def test_create_biomarker_reading(client):
    payload = {
        "source": "manual",
        "metric": "blood_pressure_systolic",
        "value": 120.0,
        "unit": "mmHg",
        "recorded_at": "2026-04-07T08:00:00",
    }
    response = client.post("/biomarkers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["metric"] == "blood_pressure_systolic"
    assert data["value"] == 120.0
    assert data["id"] is not None


def test_list_biomarker_readings(client):
    for value in [118.0, 122.0]:
        client.post("/biomarkers/", json={
            "source": "manual",
            "metric": "blood_pressure_systolic",
            "value": value,
            "unit": "mmHg",
            "recorded_at": "2026-04-07T08:00:00",
        })
    response = client.get("/biomarkers/?metric=blood_pressure_systolic")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_biomarkers_by_date_range(client):
    client.post("/biomarkers/", json={
        "source": "manual",
        "metric": "hrv",
        "value": 55.0,
        "unit": "ms",
        "recorded_at": "2026-01-01T08:00:00",
    })
    client.post("/biomarkers/", json={
        "source": "manual",
        "metric": "hrv",
        "value": 60.0,
        "unit": "ms",
        "recorded_at": "2026-04-07T08:00:00",
    })
    response = client.get("/biomarkers/?metric=hrv&from_date=2026-04-01&to_date=2026-04-30")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"] == 60.0
