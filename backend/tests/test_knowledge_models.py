from datetime import datetime

from backend.models import BeliefSnapshot, JournalEntry


def test_journal_entry_create(db):
    entry = JournalEntry(date="2026-04-08", body="Today was productive.", tags=["work", "health"], mood=8, energy=7)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    assert entry.id is not None
    assert entry.date == "2026-04-08"
    assert entry.tags == ["work", "health"]
    assert entry.mood == 8
    assert isinstance(entry.created_at, datetime)


def test_journal_entry_defaults(db):
    entry = JournalEntry(date="2026-04-09")
    db.add(entry)
    db.commit()
    db.refresh(entry)

    assert entry.body == ""
    assert entry.tags == []
    assert entry.mood is None
    assert entry.energy is None


def test_journal_entry_date_unique(db):
    db.add(JournalEntry(date="2026-04-10", body="First"))
    db.commit()
    import sqlalchemy
    db.add(JournalEntry(date="2026-04-10", body="Duplicate"))
    try:
        db.commit()
        assert False, "Should have raised"
    except sqlalchemy.exc.IntegrityError:
        db.rollback()


def test_belief_snapshot_create(db):
    snap = BeliefSnapshot(title="On exercise", body="I believe consistent Zone 2 cardio is the highest-leverage intervention.", tags=["health"])
    db.add(snap)
    db.commit()
    db.refresh(snap)

    assert snap.id is not None
    assert snap.title == "On exercise"
    assert snap.tags == ["health"]
    assert isinstance(snap.created_at, datetime)


def test_belief_snapshot_multiple_versions(db):
    for body in ["Version 1", "Version 2", "Version 3"]:
        db.add(BeliefSnapshot(title="On sleep", body=body))
    db.commit()

    from sqlalchemy import select
    rows = db.execute(select(BeliefSnapshot).where(BeliefSnapshot.title == "On sleep")).scalars().all()
    assert len(rows) == 3
