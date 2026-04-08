from backend.models import BeliefSnapshot, JournalEntry


def test_export_structure(client):
    resp = client.get("/export")
    assert resp.status_code == 200
    data = resp.json()
    assert "exported_at" in data
    assert "biomarker_readings" in data
    assert "journal_entries" in data
    assert "belief_snapshots" in data
    assert "interventions" in data
    assert "protocol_entries" in data
    assert "research_digests" in data


def test_export_includes_data(client, db):
    db.add(JournalEntry(date="2026-04-08", body="Test entry", tags=["test"]))
    db.add(BeliefSnapshot(title="On testing", body="Tests are good."))
    db.commit()

    resp = client.get("/export")
    data = resp.json()
    assert any(e["body"] == "Test entry" for e in data["journal_entries"])
    assert any(s["title"] == "On testing" for s in data["belief_snapshots"])


def test_export_empty_database(client):
    resp = client.get("/export")
    assert resp.status_code == 200
    data = resp.json()
    assert data["biomarker_readings"] == []
    assert data["journal_entries"] == []
    assert data["belief_snapshots"] == []
