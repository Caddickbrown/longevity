from unittest.mock import patch

from backend.models import Intervention, ProtocolExplanation

MOCK_EXPLANATION = {
    "explanation": "Zone 2 trains the aerobic base.",
    "why_it_matters": "Mitochondrial health is key.",
    "how_to_implement": "150 min/week at 60-70% max HR.",
    "sources": [{"title": "Attia", "url": "https://peterattia.com"}],
    "difficulty": "moderate",
}


def _add_intervention(db, name="Zone 2 Cardio"):
    i = Intervention(name=name, tier=1, evidence_grade="A", cost_tier=1, mechanism="Mitochondrial density", references="")
    db.add(i)
    db.commit()
    db.refresh(i)
    return i


def test_list_explanations_empty(client, db):
    _add_intervention(db)
    resp = client.get("/teaching/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["has_explanation"] is False


def test_get_explanation_not_found(client, db):
    i = _add_intervention(db)
    resp = client.get(f"/teaching/{i.id}")
    assert resp.status_code == 404


def test_generate_explanation_success(client, db):
    i = _add_intervention(db)
    with patch("backend.routers.teaching.generate_explanation", return_value=MOCK_EXPLANATION):
        resp = client.post(f"/teaching/generate/{i.id}")
    assert resp.status_code == 201
    assert resp.json()["difficulty"] == "moderate"


def test_generate_explanation_intervention_not_found(client):
    resp = client.post("/teaching/generate/9999")
    assert resp.status_code == 404


def test_generate_explanation_no_api_key(client, db):
    from backend.services.teaching import TeachingError
    i = _add_intervention(db)
    with patch("backend.routers.teaching.generate_explanation", side_effect=TeachingError("ANTHROPIC_API_KEY not configured")):
        resp = client.post(f"/teaching/generate/{i.id}")
    assert resp.status_code == 503


def test_generate_updates_existing(client, db):
    i = _add_intervention(db)
    db.add(ProtocolExplanation(intervention_id=i.id, **MOCK_EXPLANATION))
    db.commit()
    updated = {**MOCK_EXPLANATION, "difficulty": "easy"}
    with patch("backend.routers.teaching.generate_explanation", return_value=updated):
        resp = client.post(f"/teaching/generate/{i.id}")
    assert resp.status_code == 201
    assert resp.json()["difficulty"] == "easy"


def test_list_shows_has_explanation_true(client, db):
    i = _add_intervention(db)
    db.add(ProtocolExplanation(intervention_id=i.id, **MOCK_EXPLANATION))
    db.commit()
    resp = client.get("/teaching/")
    assert resp.json()[0]["has_explanation"] is True
