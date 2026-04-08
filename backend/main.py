from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal, get_db, init_db
from backend.models import BeliefSnapshot, BiomarkerReading, Intervention, JournalEntry, ProtocolEntry, ResearchDigest
from backend.routers import beliefs, biomarkers, blood_panel, checklist, correlation, journal, protocols, research
from backend.schemas import BeliefSnapshotOut, BiomarkerReadingOut, InterventionOut, JournalEntryOut, ProtocolEntryOut, ResearchDigestOut
from sqlalchemy import select
from backend.seed_data.protocols import seed_tier1_protocols
from backend.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_tier1_protocols(db)
    finally:
        db.close()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Longevity OS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(biomarkers.router)
app.include_router(protocols.router)
app.include_router(checklist.router)
app.include_router(research.router)
app.include_router(correlation.router)
app.include_router(blood_panel.router)
app.include_router(journal.router)
app.include_router(beliefs.router)


@app.get("/export")
def export_all(db: Session = Depends(get_db)):
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "biomarker_readings": [BiomarkerReadingOut.model_validate(r).model_dump() for r in db.execute(select(BiomarkerReading)).scalars().all()],
        "journal_entries": [JournalEntryOut.model_validate(e).model_dump() for e in db.execute(select(JournalEntry).order_by(JournalEntry.date.desc())).scalars().all()],
        "belief_snapshots": [BeliefSnapshotOut.model_validate(s).model_dump() for s in db.execute(select(BeliefSnapshot).order_by(BeliefSnapshot.created_at.desc())).scalars().all()],
        "interventions": [InterventionOut.model_validate(i).model_dump() for i in db.execute(select(Intervention)).scalars().all()],
        "protocol_entries": [ProtocolEntryOut.model_validate(p).model_dump() for p in db.execute(select(ProtocolEntry)).scalars().all()],
        "research_digests": [ResearchDigestOut.model_validate(d).model_dump() for d in db.execute(select(ResearchDigest).order_by(ResearchDigest.generated_at.desc())).scalars().all()],
    }
