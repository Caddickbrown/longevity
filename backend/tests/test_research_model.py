from datetime import datetime

from backend.models import ResearchDigest


def test_research_digest_create(db):
    digest = ResearchDigest(
        source="pubmed+claude",
        summary="NMN shows promising results in extending healthspan.",
        interventions_mentioned=["NMN", "NR"],
        raw_response='{"key_findings": []}',
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)

    assert digest.id is not None
    assert digest.source == "pubmed+claude"
    assert digest.interventions_mentioned == ["NMN", "NR"]
    assert isinstance(digest.generated_at, datetime)


def test_research_digest_defaults(db):
    digest = ResearchDigest(
        source="test",
        summary="Test summary.",
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)

    assert digest.interventions_mentioned == []
    assert digest.raw_response == ""
