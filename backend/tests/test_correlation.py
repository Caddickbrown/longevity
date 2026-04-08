from datetime import date, datetime

from backend.models import BiomarkerReading, Intervention, ProtocolEntry
from backend.services.correlation import compute_correlation


def _add_reading(db, day: str, value: float, metric: str = "sleep_total_mins"):
    db.add(BiomarkerReading(
        source="test", metric=metric, value=value, unit="min",
        recorded_at=datetime.fromisoformat(f"{day}T08:00:00"),
    ))


def _add_compliance(db, day: str, count: int):
    # Need an intervention first
    for i in range(count):
        intervention = db.merge(Intervention(
            id=i + 1, name=f"Protocol {i}", tier=1,
            evidence_grade="A", cost_tier=1, mechanism="test", references="",
        ))
        db.add(ProtocolEntry(intervention_id=i + 1, date=day, complied=True))


def test_compute_correlation_returns_data(db):
    _add_reading(db, "2026-01-01", 420.0)
    _add_reading(db, "2026-01-02", 390.0)
    _add_reading(db, "2026-01-03", 450.0)
    db.commit()

    result = compute_correlation(
        "sleep_total_mins",
        date(2026, 1, 1),
        date(2026, 1, 3),
        db,
    )
    assert result["metric"] == "sleep_total_mins"
    assert len(result["data"]) == 3
    assert all("date" in d and "value" in d and "compliance" in d for d in result["data"])


def test_compute_correlation_with_compliance(db):
    _add_reading(db, "2026-01-01", 420.0)
    _add_reading(db, "2026-01-02", 390.0)
    db.flush()
    _add_compliance(db, "2026-01-01", 3)
    db.commit()

    result = compute_correlation("sleep_total_mins", date(2026, 1, 1), date(2026, 1, 2), db)
    day1 = next(d for d in result["data"] if d["date"] == "2026-01-01")
    assert day1["compliance"] == 3


def test_compute_correlation_no_data(db):
    result = compute_correlation("sleep_total_mins", date(2026, 1, 1), date(2026, 1, 3), db)
    assert result["data"] == []
    assert result["pearson_r"] is None


def test_compute_correlation_insufficient_for_pearson(db):
    _add_reading(db, "2026-01-01", 420.0)
    db.commit()
    result = compute_correlation("sleep_total_mins", date(2026, 1, 1), date(2026, 1, 1), db)
    assert result["pearson_r"] is None


def test_compute_correlation_pearson_computed(db):
    for i, val in enumerate([300, 360, 420, 480, 540]):
        _add_reading(db, f"2026-01-0{i+1}", val)
    db.flush()
    # Add ascending compliance to get a positive correlation
    for i in range(5):
        for j in range(i):
            db.add(Intervention(id=100 + i * 10 + j, name=f"P{i}{j}", tier=1, evidence_grade="A", cost_tier=1, mechanism="", references=""))
            db.add(ProtocolEntry(intervention_id=100 + i * 10 + j, date=f"2026-01-0{i+1}", complied=True))
    db.commit()

    result = compute_correlation("sleep_total_mins", date(2026, 1, 1), date(2026, 1, 5), db)
    assert result["pearson_r"] is not None
