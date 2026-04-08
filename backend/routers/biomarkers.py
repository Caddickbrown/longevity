from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BiomarkerReading
from backend.schemas import BiomarkerReadingCreate, BiomarkerReadingOut

router = APIRouter(prefix="/biomarkers", tags=["biomarkers"])


@router.post("/", response_model=BiomarkerReadingOut, status_code=201)
def create_reading(payload: BiomarkerReadingCreate, db: Session = Depends(get_db)):
    reading = BiomarkerReading(**payload.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/", response_model=list[BiomarkerReadingOut])
def list_readings(
    metric: str | None = Query(None),
    from_date: str | None = Query(None),  # YYYY-MM-DD
    to_date: str | None = Query(None),    # YYYY-MM-DD
    db: Session = Depends(get_db),
):
    stmt = select(BiomarkerReading)
    if metric:
        stmt = stmt.where(BiomarkerReading.metric == metric)
    if from_date:
        try:
            stmt = stmt.where(BiomarkerReading.recorded_at >= datetime.fromisoformat(from_date))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid from_date format: {from_date}. Use YYYY-MM-DD.")
    if to_date:
        try:
            stmt = stmt.where(BiomarkerReading.recorded_at <= datetime.fromisoformat(to_date + "T23:59:59"))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid to_date format: {to_date}. Use YYYY-MM-DD.")
    stmt = stmt.order_by(BiomarkerReading.recorded_at.asc())
    return db.execute(stmt).scalars().all()


class BackfillRequest(BaseModel):
    days: int = 30


@router.post("/sync/backfill")
def backfill_garmin(payload: BackfillRequest, db: Session = Depends(get_db)):
    from backend.services.garmin import get_garmin_client, sync_date, GarminSyncError
    try:
        client = get_garmin_client()
    except (GarminSyncError, Exception) as e:
        raise HTTPException(status_code=503, detail=str(e))

    total = 0
    today = date.today()
    for i in range(payload.days):
        d = today - timedelta(days=i)
        total += sync_date(client, d, db)

    return {"inserted": total, "days_synced": payload.days}
