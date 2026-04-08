from datetime import datetime

from backend.models import BiomarkerReading


def _add_reading(db, day: str, value: float):
    db.add(BiomarkerReading(
        source="test", metric="resting_hr", value=value, unit="bpm",
        recorded_at=datetime.fromisoformat(f"{day}T08:00:00"),
    ))


def test_correlation_missing_metric(client):
    resp = client.get("/correlation/")
    assert resp.status_code == 422


def test_correlation_invalid_date(client):
    resp = client.get("/correlation/?metric=resting_hr&from_date=not-a-date")
    assert resp.status_code == 400


def test_correlation_from_after_to(client):
    resp = client.get("/correlation/?metric=resting_hr&from_date=2026-02-01&to_date=2026-01-01")
    assert resp.status_code == 400


def test_correlation_empty_data(client):
    resp = client.get("/correlation/?metric=resting_hr&from_date=2026-01-01&to_date=2026-01-07")
    assert resp.status_code == 200
    body = resp.json()
    assert body["metric"] == "resting_hr"
    assert body["data"] == []
    assert body["pearson_r"] is None


def test_correlation_returns_data(client, db):
    for day, val in [("2026-01-01", 58.0), ("2026-01-02", 62.0), ("2026-01-03", 55.0)]:
        _add_reading(db, day, val)
    db.commit()

    resp = client.get("/correlation/?metric=resting_hr&from_date=2026-01-01&to_date=2026-01-03")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 3
    assert body["from_date"] == "2026-01-01"
    assert body["to_date"] == "2026-01-03"
