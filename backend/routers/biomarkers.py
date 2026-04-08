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
def backfill_health_data(payload: BackfillRequest, db: Session = Depends(get_db)):
    from backend.services.health_bridge import HealthBridgeError, sync as bridge_sync
    from backend.services.garmin import GarminSyncError, get_garmin_client, sync_date as garmin_sync_date

    results = {}

    # Primary: health-at-home bridge
    try:
        inserted = bridge_sync(days=payload.days, db_session=db)
        results["health_at_home"] = inserted
    except HealthBridgeError as e:
        results["health_at_home_error"] = str(e)

    # Garmin fallback for HRV/VO2
    try:
        client = get_garmin_client()
        total = 0
        today = date.today()
        for i in range(min(payload.days, 90)):  # Garmin API limit
            d = today - timedelta(days=i)
            total += garmin_sync_date(client, d, db)
        results["garmin"] = total
    except Exception:
        results["garmin"] = 0  # Expected when no credentials or rate-limited

    return {"inserted": sum(v for v in results.values() if isinstance(v, int)), "days_synced": payload.days, "detail": results}
