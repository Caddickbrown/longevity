from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import SessionLocal, init_db
from backend.routers import biomarkers, checklist, protocols
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
    allow_origins=["http://localhost:3000", "http://100.70.55.16:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(biomarkers.router)
app.include_router(protocols.router)
app.include_router(checklist.router)
