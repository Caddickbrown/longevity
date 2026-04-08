from unittest.mock import patch

from backend.models import ResearchDigest

SAMPLE_DIGEST_DATA = {
    "source": "pubmed+claude",
    "summary": "NMN shows promising results.",
    "interventions_mentioned": ["NMN"],
    "raw_response": "{}",
}

MOCK_ARTICLES = [{"title": "NMN extends healthspan", "snippet": "", "source": "pubmed", "url": "https://pubmed.ncbi.nlm.nih.gov/1/"}]
MOCK_DIGEST = {
    "source": "pubmed+claude",
    "summary": "NMN shows promising results.",
    "interventions_mentioned": ["NMN"],
    "raw_response": "{}",
}


def test_list_digests_empty(client):
    resp = client.get("/research/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_digests_returns_latest_first(client, db):
    for i in range(3):
        db.add(ResearchDigest(source="test", summary=f"Digest {i}", interventions_mentioned=[]))
    db.commit()

    resp = client.get("/research/")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_get_digest_not_found(client):
    resp = client.get("/research/999")
    assert resp.status_code == 404


def test_get_digest_found(client, db):
    d = ResearchDigest(**SAMPLE_DIGEST_DATA)
    db.add(d)
    db.commit()
    db.refresh(d)

    resp = client.get(f"/research/{d.id}")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "NMN shows promising results."
    assert resp.json()["interventions_mentioned"] == ["NMN"]


def test_generate_digest_success(client):
    with patch("backend.routers.research.fetch_research", return_value=MOCK_ARTICLES):
        with patch("backend.routers.research.synthesise", return_value=MOCK_DIGEST):
            resp = client.post("/research/generate")
    assert resp.status_code == 201
    assert resp.json()["source"] == "pubmed+claude"


def test_generate_digest_fetch_error(client):
    from backend.services.research_fetcher import FetchError
    with patch("backend.routers.research.fetch_research", side_effect=FetchError("unreachable")):
        resp = client.post("/research/generate")
    assert resp.status_code == 503


def test_generate_digest_synthesis_error(client):
    from backend.services.research_synthesiser import SynthesisError
    with patch("backend.routers.research.fetch_research", return_value=MOCK_ARTICLES):
        with patch("backend.routers.research.synthesise", side_effect=SynthesisError("no key")):
            resp = client.post("/research/generate")
    assert resp.status_code == 503
