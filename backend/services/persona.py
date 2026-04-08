"""Assembles a rich persona context prompt from the user's accumulated data."""
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import BeliefSnapshot, BiomarkerReading, Intervention, JournalEntry

logger = logging.getLogger(__name__)

KEY_METRICS = ["resting_hr", "sleep_total_mins", "weight_kg", "hrv"]


def build_persona_context(db: Session) -> str:
    """
    Assembles a system prompt that seeds Claude with the user's personal context.
    Draws from recent journal entries, latest belief snapshots, recent biomarkers,
    and active protocols. Returns a string system prompt.
    """
    sections: list[str] = []

    sections.append(
        "You are a personal AI assistant with deep knowledge of this specific person. "
        "Use the context below to give personalised, relevant responses. "
        "Speak as someone who knows them well — not generically."
    )

    # Recent journal entries (last 30)
    journal_entries = db.execute(
        select(JournalEntry).order_by(JournalEntry.date.desc()).limit(30)
    ).scalars().all()

    if journal_entries:
        journal_text = "\n".join(
            f"  {e.date} (mood {e.mood}/10, energy {e.energy}/10): {e.body[:200]}"
            for e in journal_entries
        )
        sections.append(f"## Recent Journal Entries\n{journal_text}")

    # Latest belief snapshots (one per title, newest)
    all_beliefs = db.execute(
        select(BeliefSnapshot).order_by(BeliefSnapshot.created_at.desc())
    ).scalars().all()
    seen_titles: set[str] = set()
    latest_beliefs: list[BeliefSnapshot] = []
    for b in all_beliefs:
        if b.title not in seen_titles:
            seen_titles.add(b.title)
            latest_beliefs.append(b)

    if latest_beliefs:
        belief_text = "\n".join(f"  [{b.title}]: {b.body[:300]}" for b in latest_beliefs)
        sections.append(f"## Core Beliefs and Values\n{belief_text}")

    # Recent biomarker readings (last 7 days, key metrics)
    week_ago = date.today() - timedelta(days=7)
    recent_readings = db.execute(
        select(BiomarkerReading)
        .where(BiomarkerReading.metric.in_(KEY_METRICS))
        .where(BiomarkerReading.recorded_at >= week_ago.isoformat())
        .order_by(BiomarkerReading.recorded_at.desc())
        .limit(28)
    ).scalars().all()

    if recent_readings:
        reading_text = "\n".join(
            f"  {r.metric}: {r.value} {r.unit} ({r.recorded_at.date()})"
            for r in recent_readings
        )
        sections.append(f"## Recent Biomarker Readings (last 7 days)\n{reading_text}")

    # Active protocols
    protocols = db.execute(select(Intervention.name, Intervention.tier)).all()
    if protocols:
        protocol_text = "\n".join(f"  Tier {p.tier}: {p.name}" for p in protocols)
        sections.append(f"## Active Protocols\n{protocol_text}")

    return "\n\n".join(sections)
