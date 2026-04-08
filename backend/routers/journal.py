from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import JournalEntry
from backend.schemas import JournalEntryCreate, JournalEntryOut

router = APIRouter(prefix="/journal", tags=["journal"])


@router.post("/", response_model=JournalEntryOut)
def upsert_entry(payload: JournalEntryCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(JournalEntry).where(JournalEntry.date == payload.date)).scalar_one_or_none()
    if existing:
        for field, value in payload.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing
    entry = JournalEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/search", response_model=list[JournalEntryOut])
def search_entries(q: str = Query(...), db: Session = Depends(get_db)):
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.body.contains(q))
        .order_by(JournalEntry.date.desc())
        .limit(50)
    )
    return db.execute(stmt).scalars().all()


@router.get("/", response_model=list[JournalEntryOut])
def list_entries(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    tag: str | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(JournalEntry)
    if from_date:
        stmt = stmt.where(JournalEntry.date >= from_date)
    if to_date:
        stmt = stmt.where(JournalEntry.date <= to_date)
    if tag:
        stmt = stmt.where(JournalEntry.tags.contains(tag))
    stmt = stmt.order_by(JournalEntry.date.desc()).limit(100)
    return db.execute(stmt).scalars().all()


@router.get("/{date}", response_model=JournalEntryOut)
def get_entry(date: str, db: Session = Depends(get_db)):
    entry = db.execute(select(JournalEntry).where(JournalEntry.date == date)).scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail=f"No journal entry for {date}")
    return entry
