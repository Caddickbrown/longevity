from datetime import datetime

from backend.models import BeliefSnapshot, BiomarkerReading, Intervention, JournalEntry
from backend.services.persona import build_persona_context


def test_persona_context_empty_db(db):
    context = build_persona_context(db)
    assert "personal AI assistant" in context


def test_persona_context_includes_journal(db):
    db.add(JournalEntry(date="2026-04-08", body="Had a great run today.", mood=8, energy=9))
    db.commit()
    context = build_persona_context(db)
    assert "great run" in context
    assert "2026-04-08" in context


def test_persona_context_includes_beliefs(db):
    db.add(BeliefSnapshot(title="On exercise", body="Zone 2 is the most important thing I can do."))
    db.commit()
    context = build_persona_context(db)
    assert "Zone 2" in context
    assert "On exercise" in context


def test_persona_context_deduplicates_beliefs(db):
    db.add(BeliefSnapshot(title="On sleep", body="Version 1: 7 hours."))
    db.add(BeliefSnapshot(title="On sleep", body="Version 2: 8 hours."))
    db.commit()
    context = build_persona_context(db)
    # Only latest version should appear
    assert context.count("On sleep") == 1


def test_persona_context_includes_protocols(db):
    db.add(Intervention(name="Creatine", tier=1, evidence_grade="A", cost_tier=1, mechanism="ATP resynthesis", references=""))
    db.commit()
    context = build_persona_context(db)
    assert "Creatine" in context


def test_persona_context_includes_biomarkers(db):
    db.add(BiomarkerReading(source="garmin", metric="resting_hr", value=58.0, unit="bpm", recorded_at=datetime.now()))
    db.commit()
    context = build_persona_context(db)
    assert "resting_hr" in context
