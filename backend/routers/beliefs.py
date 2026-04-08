from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BeliefSnapshot
from backend.schemas import BeliefSnapshotCreate, BeliefSnapshotOut

router = APIRouter(prefix="/beliefs", tags=["beliefs"])


@router.post("/", response_model=BeliefSnapshotOut, status_code=201)
def create_snapshot(payload: BeliefSnapshotCreate, db: Session = Depends(get_db)):
    snap = BeliefSnapshot(**payload.model_dump())
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


@router.get("/", response_model=list[BeliefSnapshotOut])
def list_snapshots(db: Session = Depends(get_db)):
    stmt = select(BeliefSnapshot).order_by(BeliefSnapshot.created_at.desc())
    return db.execute(stmt).scalars().all()


@router.get("/by-title/{title}", response_model=list[BeliefSnapshotOut])
def get_by_title(title: str, db: Session = Depends(get_db)):
    stmt = (
        select(BeliefSnapshot)
        .where(BeliefSnapshot.title == title)
        .order_by(BeliefSnapshot.created_at.desc())
    )
    return db.execute(stmt).scalars().all()


@router.get("/{snapshot_id}", response_model=BeliefSnapshotOut)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.get(BeliefSnapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snap
