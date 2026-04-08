from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ProtocolEntry
from backend.schemas import ProtocolEntryCreate, ProtocolEntryOut

router = APIRouter(prefix="/checklist", tags=["checklist"])


@router.post("/", response_model=ProtocolEntryOut, status_code=201)
def upsert_entry(payload: ProtocolEntryCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(ProtocolEntry).where(
            ProtocolEntry.intervention_id == payload.intervention_id,
            ProtocolEntry.date == payload.date,
        )
    ).scalar_one_or_none()

    if existing:
        existing.complied = payload.complied
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing

    entry = ProtocolEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[ProtocolEntryOut])
def list_entries(date: str = Query(..., description="YYYY-MM-DD"), db: Session = Depends(get_db)):
    stmt = select(ProtocolEntry).where(ProtocolEntry.date == date)
    return db.execute(stmt).scalars().all()
