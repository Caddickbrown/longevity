from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BiomarkerReading
from backend.services.blood_panel import BloodPanelParseError, parse_blood_panel_csv

router = APIRouter(prefix="/blood-panel", tags=["blood-panel"])


@router.post("/import")
async def import_blood_panel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept a multipart CSV file upload (field name: file) and import blood panel readings.
    Deduplicates by (metric, date). Returns {"inserted": N, "skipped": N}.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    raw_bytes = await file.read()
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1")

    try:
        readings = parse_blood_panel_csv(content)
    except BloodPanelParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not readings:
        return {"inserted": 0, "skipped": 0}

    # Build set of (metric, date) pairs already in the database
    metrics_in_import = list({r["metric"] for r in readings})
    existing_rows = db.execute(
        select(BiomarkerReading.metric, BiomarkerReading.recorded_at).where(
            BiomarkerReading.metric.in_(metrics_in_import),
            BiomarkerReading.source == "blood_panel",
        )
    ).all()
    existing_keys = {(row.metric, row.recorded_at.date()) for row in existing_rows}

    inserted = 0
    skipped = 0
    for reading in readings:
        key = (reading["metric"], reading["recorded_at"].date())
        if key in existing_keys:
            skipped += 1
        else:
            db.add(BiomarkerReading(**reading))
            existing_keys.add(key)  # prevent duplicates within the same upload
            inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped}
