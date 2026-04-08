from datetime import datetime

from backend.models import Conversation, Intervention, ProtocolExplanation


def _add_intervention(db):
    i = Intervention(name="Test Protocol", tier=1, evidence_grade="A", cost_tier=1, mechanism="Test", references="")
    db.add(i)
    db.commit()
    db.refresh(i)
    return i


def test_protocol_explanation_create(db):
    i = _add_intervention(db)
    exp = ProtocolExplanation(
        intervention_id=i.id,
        explanation="Zone 2 cardio improves mitochondrial density.",
        why_it_matters="Mitochondrial health is central to longevity.",
        how_to_implement="150+ min/week at 60-70% max HR.",
        sources=[{"title": "Attia on Zone 2", "url": "https://peterattia.com"}],
        difficulty="moderate",
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    assert exp.id is not None
    assert exp.intervention_id == i.id
    assert exp.sources[0]["title"] == "Attia on Zone 2"
    assert isinstance(exp.generated_at, datetime)


def test_protocol_explanation_unique_per_intervention(db):
    i = _add_intervention(db)
    db.add(ProtocolExplanation(intervention_id=i.id, explanation="First", why_it_matters="", how_to_implement="", sources=[], difficulty="easy"))
    db.commit()
    import sqlalchemy
    db.add(ProtocolExplanation(intervention_id=i.id, explanation="Duplicate", why_it_matters="", how_to_implement="", sources=[], difficulty="easy"))
    try:
        db.commit()
        assert False, "Should have raised"
    except sqlalchemy.exc.IntegrityError:
        db.rollback()


def test_conversation_create(db):
    msg = Conversation(role="user", content="What is Zone 2 cardio?")
    db.add(msg)
    db.commit()
    db.refresh(msg)

    assert msg.id is not None
    assert msg.role == "user"
    assert isinstance(msg.created_at, datetime)


def test_conversation_roles(db):
    for role, content in [("user", "Hello"), ("assistant", "Hi there"), ("user", "Tell me more")]:
        db.add(Conversation(role=role, content=content))
    db.commit()

    from sqlalchemy import select
    rows = db.execute(select(Conversation).order_by(Conversation.created_at)).scalars().all()
    assert [r.role for r in rows] == ["user", "assistant", "user"]
