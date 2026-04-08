# Longevity OS — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web app on Raspberry Pi 5 that ingests Garmin Connect data, displays biomarker trends, supports manual BP/supplement/mood entry, and provides a daily Tier 1 protocol checklist.

**Architecture:** FastAPI backend + SQLite database, background APScheduler worker for Garmin sync, React + Vite frontend with Recharts for time-series dashboards. Everything served locally on the Pi, accessible via Tailscale.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, APScheduler, garminconnect, pytest, httpx — React 18, Vite, TypeScript, shadcn/ui, Recharts, Tailwind CSS

---

## File Structure

```
longevity/
├── backend/
│   ├── main.py                    # FastAPI app, router registration, CORS
│   ├── config.py                  # Pydantic Settings from .env
│   ├── database.py                # SQLAlchemy engine, session factory, Base
│   ├── models.py                  # ORM models: BiomarkerReading, Intervention, ProtocolEntry
│   ├── schemas.py                 # Pydantic schemas for all API I/O
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── biomarkers.py          # GET/POST BiomarkerReading endpoints
│   │   ├── protocols.py           # GET Intervention library endpoint
│   │   └── checklist.py           # GET/POST daily ProtocolEntry endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── garmin.py              # Garmin Connect login + metric extraction
│   │   └── scheduler.py           # APScheduler setup, hourly Garmin sync job
│   ├── seed_data/
│   │   ├── __init__.py
│   │   └── protocols.py           # Tier 1 protocol definitions + seed function
│   ├── tests/
│   │   ├── conftest.py            # pytest fixtures: test DB, test client, sample data
│   │   ├── test_biomarkers.py     # BiomarkerReading API tests
│   │   ├── test_protocols.py      # Protocol library + checklist API tests
│   │   └── test_garmin.py         # Garmin service tests (mocked)
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx               # React entry point
│       ├── App.tsx                # Router + layout shell
│       ├── lib/
│       │   └── api.ts             # Typed fetch wrappers for all backend endpoints
│       ├── types.ts               # TypeScript types mirroring backend schemas
│       └── pages/
│           ├── Dashboard.tsx      # Biomarker time-series charts
│           ├── Protocols.tsx      # Intervention library (tiered view)
│           └── Checklist.tsx      # Daily protocol compliance checklist
├── .env.example
└── docs/  (already exists)
```

---

## Task 1: Project Scaffold + Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `.env.example`
- Create: `backend/config.py`

- [ ] **Step 1: Create backend/requirements.txt**

```text
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.36
pydantic-settings==2.5.2
apscheduler==3.10.4
garminconnect==0.2.26
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
anthropic==0.40.0
```

- [ ] **Step 2: Create .env.example**

```bash
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=yourpassword
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///./longevity.db
```

- [ ] **Step 3: Create backend/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    garmin_email: str = ""
    garmin_password: str = ""
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./longevity.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
```

- [ ] **Step 4: Install dependencies**

```bash
cd /home/dcb/longevity
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Copy .env.example to .env and fill in credentials**

```bash
cp .env.example .env
# Edit .env with your Garmin email/password and Anthropic API key
```

- [ ] **Step 6: Commit**

```bash
cd /home/dcb/longevity
git init
git add backend/requirements.txt .env.example backend/config.py
git commit -m "feat: project scaffold and config"
```

---

## Task 2: Database Setup

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///./test_longevity.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Create `backend/tests/test_biomarkers.py` with initial import test:

```python
from backend.models import BiomarkerReading
from backend.database import Base


def test_biomarker_table_exists(db):
    tables = Base.metadata.tables.keys()
    assert "biomarker_readings" in tables
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/dcb/longevity
source .venv/bin/activate
pytest backend/tests/test_biomarkers.py::test_biomarker_table_exists -v
```

Expected: `ModuleNotFoundError` — database.py and models.py don't exist yet.

- [ ] **Step 3: Create backend/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Create backend/models.py**

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class BiomarkerReading(Base):
    __tablename__ = "biomarker_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(50))  # garmin | manual | import
    metric: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    tier: Mapped[int] = mapped_column(Integer)          # 1, 2, or 3
    evidence_grade: Mapped[str] = mapped_column(String(1))  # A, B, or C
    cost_tier: Mapped[int] = mapped_column(Integer)     # 1=£, 2=££, 3=£££
    mechanism: Mapped[str] = mapped_column(Text)
    references: Mapped[str] = mapped_column(Text, default="")  # newline-separated URLs
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProtocolEntry(Base):
    __tablename__ = "protocol_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intervention_id: Mapped[int] = mapped_column(Integer, index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    complied: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 5: Create backend/main.py (minimal)**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Longevity OS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://100.70.55.16:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest backend/tests/test_biomarkers.py::test_biomarker_table_exists -v
```

Expected: `PASSED`

- [ ] **Step 7: Commit**

```bash
git add backend/database.py backend/models.py backend/main.py backend/tests/conftest.py backend/tests/test_biomarkers.py
git commit -m "feat: database setup with BiomarkerReading, Intervention, ProtocolEntry models"
```

---

## Task 3: Biomarker API

**Files:**
- Create: `backend/schemas.py`
- Create: `backend/routers/biomarkers.py`
- Modify: `backend/main.py` (register router)
- Test: `backend/tests/test_biomarkers.py`

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/test_biomarkers.py`:

```python
from datetime import datetime


def test_create_biomarker_reading(client):
    payload = {
        "source": "manual",
        "metric": "blood_pressure_systolic",
        "value": 120.0,
        "unit": "mmHg",
        "recorded_at": "2026-04-07T08:00:00",
    }
    response = client.post("/biomarkers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["metric"] == "blood_pressure_systolic"
    assert data["value"] == 120.0
    assert data["id"] is not None


def test_list_biomarker_readings(client):
    # Seed two readings
    for value in [118.0, 122.0]:
        client.post("/biomarkers/", json={
            "source": "manual",
            "metric": "blood_pressure_systolic",
            "value": value,
            "unit": "mmHg",
            "recorded_at": "2026-04-07T08:00:00",
        })
    response = client.get("/biomarkers/?metric=blood_pressure_systolic")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_biomarkers_by_date_range(client):
    client.post("/biomarkers/", json={
        "source": "manual",
        "metric": "hrv",
        "value": 55.0,
        "unit": "ms",
        "recorded_at": "2026-01-01T08:00:00",
    })
    client.post("/biomarkers/", json={
        "source": "manual",
        "metric": "hrv",
        "value": 60.0,
        "unit": "ms",
        "recorded_at": "2026-04-07T08:00:00",
    })
    response = client.get("/biomarkers/?metric=hrv&from_date=2026-04-01&to_date=2026-04-30")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"] == 60.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_biomarkers.py -v -k "not test_biomarker_table"
```

Expected: `404 Not Found` errors — router not registered yet.

- [ ] **Step 3: Create backend/schemas.py**

```python
from datetime import datetime

from pydantic import BaseModel


class BiomarkerReadingCreate(BaseModel):
    source: str
    metric: str
    value: float
    unit: str
    recorded_at: datetime


class BiomarkerReadingOut(BiomarkerReadingCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InterventionOut(BaseModel):
    id: int
    name: str
    tier: int
    evidence_grade: str
    cost_tier: int
    mechanism: str
    references: str
    started_at: datetime | None
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class ProtocolEntryCreate(BaseModel):
    intervention_id: int
    date: str  # YYYY-MM-DD
    complied: bool
    notes: str = ""


class ProtocolEntryOut(ProtocolEntryCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Create backend/routers/__init__.py**

```python
```

(empty file)

- [ ] **Step 5: Create backend/routers/biomarkers.py**

```python
from datetime import datetime

from fastapi import APIRouter, Depends, Query
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
        stmt = stmt.where(BiomarkerReading.recorded_at >= datetime.fromisoformat(from_date))
    if to_date:
        stmt = stmt.where(BiomarkerReading.recorded_at <= datetime.fromisoformat(to_date + "T23:59:59"))
    stmt = stmt.order_by(BiomarkerReading.recorded_at.asc())
    return db.execute(stmt).scalars().all()
```

- [ ] **Step 6: Register router in backend/main.py**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import biomarkers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Longevity OS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://100.70.55.16:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(biomarkers.router)
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest backend/tests/test_biomarkers.py -v
```

Expected: all 4 tests `PASSED`

- [ ] **Step 8: Commit**

```bash
git add backend/schemas.py backend/routers/ backend/main.py
git commit -m "feat: biomarker readings API with metric + date range filtering"
```

---

## Task 4: Protocol + Checklist API

**Files:**
- Create: `backend/routers/protocols.py`
- Create: `backend/routers/checklist.py`
- Create: `backend/seed_data/__init__.py`
- Create: `backend/seed_data/protocols.py`
- Modify: `backend/main.py` (register routers)
- Test: `backend/tests/test_protocols.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_protocols.py`:

```python
def test_list_interventions_empty(client):
    response = client.get("/protocols/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_interventions_by_tier(client):
    # Seed via the seed function directly
    from backend.seed_data.protocols import seed_tier1_protocols
    from backend.database import get_db
    db = next(get_db())
    seed_tier1_protocols(db)

    response = client.get("/protocols/?tier=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(i["tier"] == 1 for i in data)


def test_create_and_get_checklist_entry(client):
    from backend.seed_data.protocols import seed_tier1_protocols
    from backend.database import get_db
    db = next(get_db())
    seed_tier1_protocols(db)

    interventions = client.get("/protocols/").json()
    first_id = interventions[0]["id"]

    payload = {
        "intervention_id": first_id,
        "date": "2026-04-07",
        "complied": True,
        "notes": "Took with breakfast",
    }
    response = client.post("/checklist/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["complied"] is True

    response = client.get("/checklist/?date=2026-04-07")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_upsert_checklist_entry(client):
    from backend.seed_data.protocols import seed_tier1_protocols
    from backend.database import get_db
    db = next(get_db())
    seed_tier1_protocols(db)

    interventions = client.get("/protocols/").json()
    first_id = interventions[0]["id"]

    # Create
    client.post("/checklist/", json={
        "intervention_id": first_id,
        "date": "2026-04-07",
        "complied": False,
        "notes": "",
    })

    # Update (upsert)
    response = client.post("/checklist/", json={
        "intervention_id": first_id,
        "date": "2026-04-07",
        "complied": True,
        "notes": "Done",
    })
    assert response.status_code == 201
    assert response.json()["complied"] is True

    # Should still be 1 record
    entries = client.get("/checklist/?date=2026-04-07").json()
    assert len(entries) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_protocols.py -v
```

Expected: `404 Not Found` and `ModuleNotFoundError` failures.

- [ ] **Step 3: Create backend/seed_data/__init__.py**

```python
```

(empty)

- [ ] **Step 4: Create backend/seed_data/protocols.py**

```python
from sqlalchemy.orm import Session

from backend.models import Intervention

TIER_1_PROTOCOLS = [
    {
        "name": "Sleep: 7-9 hours, consistent timing",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Sleep is the single most impactful longevity behaviour. During deep sleep, the glymphatic system clears amyloid-beta and tau. Consistent circadian timing reduces cortisol dysregulation and improves insulin sensitivity.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4517023/\nhttps://examine.com/topics/sleep/",
    },
    {
        "name": "Sleep: Dark, cool room + no screens 1hr before bed",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Blue light suppresses melatonin secretion. Room temperature 18-19°C optimises sleep architecture. Blackout curtains or eye mask improve deep sleep percentage.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6751071/",
    },
    {
        "name": "Exercise: Zone 2 cardio 150+ min/week",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Zone 2 (conversational pace, ~60-70% max HR) drives mitochondrial biogenesis, improves metabolic flexibility, raises VO2 max — the strongest predictor of all-cause mortality. 150 min/week is the minimum effective dose.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7296389/\nhttps://peterattiamd.com/category/exercise/",
    },
    {
        "name": "Exercise: Strength training 2x/week",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Muscle mass is a strong predictor of longevity independent of cardiovascular fitness. Resistance training improves insulin sensitivity, bone density, and maintains functional independence. Modify for arm physio — focus on legs and core.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5863730/",
    },
    {
        "name": "Diet: Protein 1.6g/kg bodyweight daily",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Adequate protein preserves muscle mass during aging (sarcopenia prevention). 1.6g/kg is the evidence-based minimum for muscle protein synthesis. Distribute across meals for best absorption.",
        "references": "https://examine.com/topics/protein-intake/",
    },
    {
        "name": "Diet: Mediterranean-adjacent whole foods",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Mediterranean diet has the strongest human evidence for reduced all-cause mortality, cardiovascular disease, and cognitive decline. Key features: olive oil, fish, vegetables, legumes, minimal ultra-processed food.",
        "references": "https://www.nejm.org/doi/full/10.1056/nejmoa1200303",
    },
    {
        "name": "Supplement: Omega-3 (cod liver oil / fish oil)",
        "tier": 1,
        "evidence_grade": "B",
        "cost_tier": 1,
        "mechanism": "EPA/DHA reduce systemic inflammation (lowered IL-6, TNF-alpha), improve endothelial function, and have modest cardiovascular benefits. Cod liver oil also provides Vitamin D and Vitamin A. Aim for 2g combined EPA+DHA daily.",
        "references": "https://examine.com/supplements/fish-oil/",
    },
    {
        "name": "Supplement: Magnesium glycinate 400mg before bed",
        "tier": 1,
        "evidence_grade": "B",
        "cost_tier": 1,
        "mechanism": "Magnesium is a cofactor in 300+ enzymatic reactions. ~60% of adults are deficient. Glycinate form is well-absorbed and calming. Improves sleep quality (particularly deep sleep), reduces cortisol, supports cardiovascular health.",
        "references": "https://examine.com/supplements/magnesium/",
    },
    {
        "name": "Supplement: Creatine monohydrate 5g daily",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Most researched sports supplement with strong safety profile. Supports muscle protein synthesis, ATP regeneration, and has emerging evidence for cognitive benefits and neuroprotection. One of the best evidence-to-cost ratios in longevity supplementation.",
        "references": "https://examine.com/supplements/creatine/",
    },
    {
        "name": "Supplement: Review existing multivitamin for gaps",
        "tier": 1,
        "evidence_grade": "B",
        "cost_tier": 1,
        "mechanism": "Most multivitamins are poorly dosed. Check for: Vitamin D3 (1000-4000 IU), K2 MK-7 (100-200mcg), Zinc, B12. Avoid excessive iron unless deficient. Once blood panels are available (Tier 2), optimise based on data.",
        "references": "https://examine.com/supplements/multivitamin/",
    },
]


def seed_tier1_protocols(db: Session) -> None:
    existing = db.query(Intervention).filter(Intervention.tier == 1).count()
    if existing > 0:
        return
    for protocol in TIER_1_PROTOCOLS:
        db.add(Intervention(**protocol))
    db.commit()
```

- [ ] **Step 5: Create backend/routers/protocols.py**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Intervention
from backend.schemas import InterventionOut

router = APIRouter(prefix="/protocols", tags=["protocols"])


@router.get("/", response_model=list[InterventionOut])
def list_interventions(
    tier: int | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Intervention)
    if tier is not None:
        stmt = stmt.where(Intervention.tier == tier)
    stmt = stmt.order_by(Intervention.tier.asc(), Intervention.name.asc())
    return db.execute(stmt).scalars().all()
```

- [ ] **Step 6: Create backend/routers/checklist.py**

```python
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
```

- [ ] **Step 7: Register routers in backend/main.py**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import biomarkers, protocols, checklist
from backend.seed_data.protocols import seed_tier1_protocols


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from backend.database import SessionLocal
    with SessionLocal() as db:
        seed_tier1_protocols(db)
    yield


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
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
pytest backend/tests/test_protocols.py -v
```

Expected: all 4 tests `PASSED`

- [ ] **Step 9: Commit**

```bash
git add backend/routers/protocols.py backend/routers/checklist.py backend/seed_data/ backend/main.py backend/tests/test_protocols.py
git commit -m "feat: protocol library and daily checklist API with Tier 1 seed data"
```

---

## Task 5: Garmin Connect Service

**Files:**
- Create: `backend/services/__init__.py`
- Create: `backend/services/garmin.py`
- Test: `backend/tests/test_garmin.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_garmin.py`:

```python
from datetime import date
from unittest.mock import MagicMock, patch

from backend.services.garmin import extract_metrics, GarminSyncError


def _mock_garmin_api():
    api = MagicMock()
    api.get_stats.return_value = {
        "totalSteps": 8500,
        "restingHeartRate": 58,
        "averageStressLevel": 32,
        "bodyBatteryChargedValue": 85,
    }
    api.get_sleep_data.return_value = {
        "dailySleepDTO": {
            "sleepScore": 76,
            "deepSleepSeconds": 5400,
            "lightSleepSeconds": 12600,
            "remSleepSeconds": 7200,
            "awakeSleepSeconds": 900,
        }
    }
    api.get_hrv_data.return_value = {
        "hrvSummary": {
            "lastNight": 52,
        }
    }
    api.get_body_composition.return_value = {
        "totalAverage": {
            "weight": 78.5,
            "bodyFatPercentage": 18.2,
        }
    }
    return api


def test_extract_metrics_returns_readings():
    api = _mock_garmin_api()
    readings = extract_metrics(api, date(2026, 4, 7))
    metrics = {r["metric"] for r in readings}
    assert "steps" in metrics
    assert "resting_hr" in metrics
    assert "sleep_score" in metrics
    assert "hrv_last_night" in metrics
    assert "weight_kg" in metrics
    assert "body_fat_pct" in metrics


def test_extract_metrics_skips_none_values():
    api = _mock_garmin_api()
    api.get_stats.return_value = {"totalSteps": None, "restingHeartRate": 58}
    api.get_sleep_data.return_value = {"dailySleepDTO": None}
    api.get_hrv_data.return_value = {"hrvSummary": None}
    api.get_body_composition.return_value = {"totalAverage": None}

    readings = extract_metrics(api, date(2026, 4, 7))
    metrics = {r["metric"] for r in readings}
    assert "steps" not in metrics
    assert "resting_hr" in metrics


def test_extract_metrics_correct_units():
    api = _mock_garmin_api()
    readings = extract_metrics(api, date(2026, 4, 7))
    hrv = next(r for r in readings if r["metric"] == "hrv_last_night")
    assert hrv["unit"] == "ms"
    weight = next(r for r in readings if r["metric"] == "weight_kg")
    assert weight["unit"] == "kg"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_garmin.py -v
```

Expected: `ModuleNotFoundError` — garmin.py doesn't exist.

- [ ] **Step 3: Create backend/services/__init__.py**

```python
```

(empty)

- [ ] **Step 4: Create backend/services/garmin.py**

```python
from datetime import date, datetime
from typing import Any

from garminconnect import Garmin

from backend.config import settings


class GarminSyncError(Exception):
    pass


def get_garmin_client() -> Garmin:
    if not settings.garmin_email or not settings.garmin_password:
        raise GarminSyncError("GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
    client = Garmin(email=settings.garmin_email, password=settings.garmin_password)
    client.login()
    return client


def _safe_get(data: dict | None, *keys: str) -> Any:
    """Safely traverse nested dict keys, returning None if any key is missing."""
    if data is None:
        return None
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
        if data is None:
            return None
    return data


def extract_metrics(api: Garmin, for_date: date) -> list[dict]:
    """
    Extract all available biomarker metrics from Garmin API for a given date.
    Returns list of dicts ready to create BiomarkerReading records.
    Skips any metric where the API returns None.
    """
    date_str = for_date.isoformat()
    recorded_at = datetime.combine(for_date, datetime.min.time())
    readings = []

    def add(metric: str, value: Any, unit: str) -> None:
        if value is not None:
            readings.append({
                "source": "garmin",
                "metric": metric,
                "value": float(value),
                "unit": unit,
                "recorded_at": recorded_at,
            })

    # Daily stats
    stats = api.get_stats(date_str)
    add("steps", _safe_get(stats, "totalSteps"), "count")
    add("resting_hr", _safe_get(stats, "restingHeartRate"), "bpm")
    add("stress", _safe_get(stats, "averageStressLevel"), "score")
    add("body_battery", _safe_get(stats, "bodyBatteryChargedValue"), "score")

    # Sleep
    sleep = api.get_sleep_data(date_str)
    sleep_dto = _safe_get(sleep, "dailySleepDTO")
    add("sleep_score", _safe_get(sleep_dto, "sleepScore"), "score")
    add("deep_sleep_seconds", _safe_get(sleep_dto, "deepSleepSeconds"), "seconds")
    add("light_sleep_seconds", _safe_get(sleep_dto, "lightSleepSeconds"), "seconds")
    add("rem_sleep_seconds", _safe_get(sleep_dto, "remSleepSeconds"), "seconds")

    # HRV
    hrv = api.get_hrv_data(date_str)
    add("hrv_last_night", _safe_get(hrv, "hrvSummary", "lastNight"), "ms")

    # Body composition
    body = api.get_body_composition(date_str)
    body_avg = _safe_get(body, "totalAverage")
    add("weight_kg", _safe_get(body_avg, "weight"), "kg")
    add("body_fat_pct", _safe_get(body_avg, "bodyFatPercentage"), "%")

    return readings


def sync_date(api: Garmin, for_date: date, db_session) -> int:
    """
    Sync one day of Garmin data into the database.
    Skips metrics that already exist for that date.
    Returns count of new readings inserted.
    """
    from sqlalchemy import select
    from backend.models import BiomarkerReading

    metrics = extract_metrics(api, for_date)
    date_str = for_date.isoformat()

    existing = set(
        db_session.execute(
            select(BiomarkerReading.metric).where(
                BiomarkerReading.source == "garmin",
                BiomarkerReading.recorded_at >= datetime.fromisoformat(date_str),
                BiomarkerReading.recorded_at < datetime.fromisoformat(date_str + "T23:59:59"),
            )
        ).scalars().all()
    )

    inserted = 0
    for reading in metrics:
        if reading["metric"] not in existing:
            db_session.add(BiomarkerReading(**reading))
            inserted += 1

    db_session.commit()
    return inserted
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest backend/tests/test_garmin.py -v
```

Expected: all 3 tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add backend/services/ backend/tests/test_garmin.py
git commit -m "feat: Garmin Connect service with metric extraction and dedup sync"
```

---

## Task 6: Background Scheduler (Hourly Garmin Sync)

**Files:**
- Create: `backend/services/scheduler.py`
- Modify: `backend/main.py` (start scheduler on lifespan)

- [ ] **Step 1: Create backend/services/scheduler.py**

```python
import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import SessionLocal

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def sync_garmin_today() -> None:
    from backend.services.garmin import get_garmin_client, sync_date, GarminSyncError
    try:
        client = get_garmin_client()
        with SessionLocal() as db:
            today = date.today()
            yesterday = today - timedelta(days=1)
            inserted_today = sync_date(client, today, db)
            inserted_yesterday = sync_date(client, yesterday, db)
            logger.info(
                "Garmin sync complete: %d new readings today, %d yesterday",
                inserted_today,
                inserted_yesterday,
            )
    except GarminSyncError as e:
        logger.warning("Garmin sync skipped: %s", e)
    except Exception:
        logger.exception("Garmin sync failed unexpectedly")


def start_scheduler() -> None:
    scheduler.add_job(sync_garmin_today, "interval", hours=1, id="garmin_sync", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — Garmin sync every hour")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
```

- [ ] **Step 2: Update backend/main.py to start/stop scheduler**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import biomarkers, protocols, checklist
from backend.seed_data.protocols import seed_tier1_protocols
from backend.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from backend.database import SessionLocal
    with SessionLocal() as db:
        seed_tier1_protocols(db)
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
```

- [ ] **Step 3: Verify the server starts without error**

```bash
cd /home/dcb/longevity
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected: server starts, logs show "Scheduler started", no errors. Visit `http://localhost:8000/docs` — FastAPI Swagger UI should load.

- [ ] **Step 4: Trigger a manual sync to verify Garmin connection**

```bash
# In a second terminal with venv activated:
python3 -c "
from backend.services.scheduler import sync_garmin_today
sync_garmin_today()
print('Sync complete')
"
```

Expected: logs show readings inserted (or "Garmin sync skipped" if credentials not set yet).

- [ ] **Step 5: Commit**

```bash
git add backend/services/scheduler.py backend/main.py
git commit -m "feat: APScheduler background worker for hourly Garmin sync"
```

---

## Task 7: Garmin Historical Backfill Endpoint

**Files:**
- Modify: `backend/routers/biomarkers.py` (add backfill endpoint)

- [ ] **Step 1: Add test**

Append to `backend/tests/test_biomarkers.py`:

```python
def test_backfill_endpoint_exists(client):
    # With no Garmin credentials, should return 503 (not 404)
    response = client.post("/biomarkers/sync/backfill", json={"days": 7})
    assert response.status_code in (200, 503)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest backend/tests/test_biomarkers.py::test_backfill_endpoint_exists -v
```

Expected: `FAIL` — 404, endpoint doesn't exist.

- [ ] **Step 3: Add backfill endpoint to backend/routers/biomarkers.py**

Add to the end of the file (after existing routes):

```python
from datetime import date, timedelta

from fastapi import HTTPException
from pydantic import BaseModel


class BackfillRequest(BaseModel):
    days: int = 30


@router.post("/sync/backfill")
def backfill_garmin(payload: BackfillRequest, db: Session = Depends(get_db)):
    from backend.services.garmin import get_garmin_client, sync_date, GarminSyncError
    try:
        client = get_garmin_client()
    except GarminSyncError as e:
        raise HTTPException(status_code=503, detail=str(e))

    total = 0
    today = date.today()
    for i in range(payload.days):
        d = today - timedelta(days=i)
        total += sync_date(client, d, db)

    return {"inserted": total, "days_synced": payload.days}
```

Also add the missing imports at the top of `backend/routers/biomarkers.py`. The full file should have:

```python
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
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(BiomarkerReading)
    if metric:
        stmt = stmt.where(BiomarkerReading.metric == metric)
    if from_date:
        stmt = stmt.where(BiomarkerReading.recorded_at >= datetime.fromisoformat(from_date))
    if to_date:
        stmt = stmt.where(BiomarkerReading.recorded_at <= datetime.fromisoformat(to_date + "T23:59:59"))
    stmt = stmt.order_by(BiomarkerReading.recorded_at.asc())
    return db.execute(stmt).scalars().all()


class BackfillRequest(BaseModel):
    days: int = 30


@router.post("/sync/backfill")
def backfill_garmin(payload: BackfillRequest, db: Session = Depends(get_db)):
    from backend.services.garmin import get_garmin_client, sync_date, GarminSyncError
    try:
        client = get_garmin_client()
    except GarminSyncError as e:
        raise HTTPException(status_code=503, detail=str(e))

    total = 0
    today = date.today()
    for i in range(payload.days):
        d = today - timedelta(days=i)
        total += sync_date(client, d, db)

    return {"inserted": total, "days_synced": payload.days}
```

- [ ] **Step 4: Run all tests**

```bash
pytest backend/tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/routers/biomarkers.py
git commit -m "feat: Garmin historical backfill endpoint"
```

---

## Task 8: Frontend Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Scaffold the Vite + React project**

```bash
cd /home/dcb/longevity
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install UI dependencies**

```bash
cd /home/dcb/longevity/frontend
npm install recharts @radix-ui/react-tabs @radix-ui/react-slot class-variance-authority clsx tailwind-merge lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: Install shadcn/ui**

```bash
cd /home/dcb/longevity/frontend
npx shadcn@latest init
```

When prompted:
- Style: Default
- Base color: Neutral
- CSS variables: Yes

Then add required components:

```bash
npx shadcn@latest add button card badge tabs checkbox textarea
```

- [ ] **Step 4: Update frontend/vite.config.ts to proxy API**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/biomarkers': 'http://localhost:8000',
      '/protocols': 'http://localhost:8000',
      '/checklist': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 5: Create frontend/src/types.ts**

```typescript
export interface BiomarkerReading {
  id: number
  source: string
  metric: string
  value: number
  unit: string
  recorded_at: string
  created_at: string
}

export interface Intervention {
  id: number
  name: string
  tier: number
  evidence_grade: string
  cost_tier: number
  mechanism: string
  references: string
  started_at: string | null
  ended_at: string | null
}

export interface ProtocolEntry {
  id: number
  intervention_id: number
  date: string
  complied: boolean
  notes: string
  created_at: string
}
```

- [ ] **Step 6: Create frontend/src/lib/api.ts**

```typescript
import type { BiomarkerReading, Intervention, ProtocolEntry } from '@/types'

const BASE = ''  // proxied through Vite to :8000

export async function getBiomarkers(params: {
  metric?: string
  from_date?: string
  to_date?: string
}): Promise<BiomarkerReading[]> {
  const query = new URLSearchParams()
  if (params.metric) query.set('metric', params.metric)
  if (params.from_date) query.set('from_date', params.from_date)
  if (params.to_date) query.set('to_date', params.to_date)
  const res = await fetch(`${BASE}/biomarkers/?${query}`)
  if (!res.ok) throw new Error('Failed to fetch biomarkers')
  return res.json()
}

export async function createBiomarker(data: Omit<BiomarkerReading, 'id' | 'created_at'>): Promise<BiomarkerReading> {
  const res = await fetch(`${BASE}/biomarkers/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to create reading')
  return res.json()
}

export async function getProtocols(tier?: number): Promise<Intervention[]> {
  const query = tier !== undefined ? `?tier=${tier}` : ''
  const res = await fetch(`${BASE}/protocols/${query}`)
  if (!res.ok) throw new Error('Failed to fetch protocols')
  return res.json()
}

export async function getChecklist(date: string): Promise<ProtocolEntry[]> {
  const res = await fetch(`${BASE}/checklist/?date=${date}`)
  if (!res.ok) throw new Error('Failed to fetch checklist')
  return res.json()
}

export async function upsertChecklistEntry(data: {
  intervention_id: number
  date: string
  complied: boolean
  notes?: string
}): Promise<ProtocolEntry> {
  const res = await fetch(`${BASE}/checklist/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes: '', ...data }),
  })
  if (!res.ok) throw new Error('Failed to save checklist entry')
  return res.json()
}

export async function triggerBackfill(days: number): Promise<{ inserted: number; days_synced: number }> {
  const res = await fetch(`${BASE}/biomarkers/sync/backfill`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ days }),
  })
  if (!res.ok) throw new Error('Backfill failed')
  return res.json()
}
```

- [ ] **Step 7: Create frontend/src/App.tsx**

```typescript
import { useState } from 'react'
import { Dashboard } from '@/pages/Dashboard'
import { Protocols } from '@/pages/Protocols'
import { Checklist } from '@/pages/Checklist'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight">Longevity OS</h1>
      </header>
      <main className="px-6 py-6">
        <Tabs defaultValue="dashboard">
          <TabsList className="mb-6">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="checklist">Today</TabsTrigger>
            <TabsTrigger value="protocols">Protocols</TabsTrigger>
          </TabsList>
          <TabsContent value="dashboard"><Dashboard /></TabsContent>
          <TabsContent value="checklist"><Checklist /></TabsContent>
          <TabsContent value="protocols"><Protocols /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
```

- [ ] **Step 8: Verify the frontend builds without errors**

```bash
cd /home/dcb/longevity/frontend
npm run build
```

Expected: build completes with no TypeScript or Vite errors.

- [ ] **Step 9: Commit**

```bash
cd /home/dcb/longevity
git add frontend/
git commit -m "feat: React + Vite frontend scaffold with shadcn/ui, types, and API client"
```

---

## Task 9: Dashboard Page (Biomarker Charts)

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Create frontend/src/pages/Dashboard.tsx**

```typescript
import { memo, useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getBiomarkers, triggerBackfill } from '@/lib/api'
import type { BiomarkerReading } from '@/types'

const METRICS = [
  { key: 'hrv_last_night', label: 'HRV', unit: 'ms', color: '#6366f1' },
  { key: 'resting_hr', label: 'Resting HR', unit: 'bpm', color: '#f43f5e' },
  { key: 'sleep_score', label: 'Sleep Score', unit: '', color: '#8b5cf6' },
  { key: 'steps', label: 'Steps', unit: '', color: '#10b981' },
  { key: 'weight_kg', label: 'Weight', unit: 'kg', color: '#f59e0b' },
  { key: 'body_fat_pct', label: 'Body Fat', unit: '%', color: '#ef4444' },
  { key: 'stress', label: 'Stress', unit: '', color: '#f97316' },
  { key: 'body_battery', label: 'Body Battery', unit: '', color: '#3b82f6' },
]

const MetricCard = memo(function MetricCard({ metricKey, label, unit, color }: { metricKey: string; label: string; unit: string; color: string }) {
  const [data, setData] = useState<BiomarkerReading[]>([])

  useEffect(() => {
    const to = new Date().toISOString().split('T')[0]
    const from = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    getBiomarkers({ metric: metricKey, from_date: from, to_date: to })
      .then(setData)
      .catch(console.error)
  }, [metricKey])

  const chartData = data.map(r => ({
    date: r.recorded_at.split('T')[0],
    value: r.value,
  }))

  const latest = data.at(-1)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        {latest && (
          <p className="text-2xl font-bold">
            {latest.value.toFixed(1)}{unit && <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>}
          </p>
        )}
        {!latest && <p className="text-sm text-muted-foreground">No data yet</p>}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={80}>
          <LineChart data={chartData}>
            <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
            <XAxis dataKey="date" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(v: number) => [`${v.toFixed(1)}${unit}`, label]}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
})

export function Dashboard() {
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)

  async function handleBackfill() {
    setSyncing(true)
    setSyncResult(null)
    try {
      const result = await triggerBackfill(30)
      setSyncResult(`Synced ${result.days_synced} days — ${result.inserted} new readings`)
    } catch (e) {
      setSyncResult('Sync failed — check Garmin credentials in .env')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Biomarkers — Last 30 Days</h2>
        <div className="flex items-center gap-3">
          {syncResult && <p className="text-sm text-muted-foreground">{syncResult}</p>}
          <Button variant="outline" size="sm" onClick={handleBackfill} disabled={syncing}>
            {syncing ? 'Syncing...' : 'Sync Garmin'}
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {METRICS.map(m => (
          <MetricCard key={m.key} metricKey={m.key} label={m.label} unit={m.unit} color={m.color} />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify it builds**

```bash
cd /home/dcb/longevity/frontend
npm run build
```

Expected: no TypeScript errors.

- [ ] **Step 3: Commit**

```bash
cd /home/dcb/longevity
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat: biomarker dashboard with 8 metric cards and 30-day sparklines"
```

---

## Task 10: Daily Checklist Page

**Files:**
- Create: `frontend/src/pages/Checklist.tsx`

- [ ] **Step 1: Create frontend/src/pages/Checklist.tsx**

```typescript
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { getProtocols, getChecklist, upsertChecklistEntry } from '@/lib/api'
import type { Intervention, ProtocolEntry } from '@/types'

const EVIDENCE_COLOUR: Record<string, string> = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-yellow-100 text-yellow-800',
  C: 'bg-orange-100 text-orange-800',
}

function toDateString(d: Date): string {
  return d.toISOString().split('T')[0]
}

export function Checklist() {
  const today = toDateString(new Date())
  const [protocols, setProtocols] = useState<Intervention[]>([])
  const [entries, setEntries] = useState<Map<number, ProtocolEntry>>(new Map())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getProtocols(1),
      getChecklist(today),
    ]).then(([protos, checklistEntries]) => {
      setProtocols(protos)
      setEntries(new Map(checklistEntries.map(e => [e.intervention_id, e])))
      setLoading(false)
    })
  }, [today])

  async function toggle(intervention: Intervention) {
    const current = entries.get(intervention.id)
    const newComplied = !(current?.complied ?? false)
    const updated = await upsertChecklistEntry({
      intervention_id: intervention.id,
      date: today,
      complied: newComplied,
    })
    setEntries(prev => new Map(prev).set(intervention.id, updated))
  }

  const completed = [...entries.values()].filter(e => e.complied).length
  const total = protocols.length

  if (loading) return <p className="text-muted-foreground text-sm">Loading...</p>

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Today — {today}</h2>
        <span className="text-sm text-muted-foreground">{completed}/{total} complete</span>
      </div>

      <div className="w-full bg-muted rounded-full h-2">
        <div
          className="bg-primary h-2 rounded-full transition-all"
          style={{ width: `${total > 0 ? (completed / total) * 100 : 0}%` }}
        />
      </div>

      <div className="space-y-2">
        {protocols.map(protocol => {
          const entry = entries.get(protocol.id)
          const done = entry?.complied ?? false
          return (
            <Card
              key={protocol.id}
              className={`cursor-pointer transition-colors ${done ? 'opacity-60' : ''}`}
              onClick={() => toggle(protocol)}
            >
              <CardContent className="flex items-start gap-3 py-3">
                <Checkbox checked={done} className="mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${done ? 'line-through text-muted-foreground' : ''}`}>
                    {protocol.name}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                    {protocol.mechanism}
                  </p>
                </div>
                <Badge className={`text-xs shrink-0 ${EVIDENCE_COLOUR[protocol.evidence_grade] ?? ''}`} variant="outline">
                  {protocol.evidence_grade}
                </Badge>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Build to verify no errors**

```bash
cd /home/dcb/longevity/frontend
npm run build
```

- [ ] **Step 3: Commit**

```bash
cd /home/dcb/longevity
git add frontend/src/pages/Checklist.tsx
git commit -m "feat: daily protocol checklist with progress bar and evidence badges"
```

---

## Task 11: Protocol Library Page

**Files:**
- Create: `frontend/src/pages/Protocols.tsx`

- [ ] **Step 1: Create frontend/src/pages/Protocols.tsx**

```typescript
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { getProtocols } from '@/lib/api'
import type { Intervention } from '@/types'

const TIER_LABEL: Record<number, string> = {
  1: 'Tier 1 — Low cost, strong evidence (start now)',
  2: 'Tier 2 — Moderate cost (when Tier 1 is stable)',
  3: 'Tier 3 — Experimental (monitor the science)',
}

const COST_LABEL: Record<number, string> = { 1: '£', 2: '££', 3: '£££' }

const EVIDENCE_COLOUR: Record<string, string> = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-yellow-100 text-yellow-800',
  C: 'bg-orange-100 text-orange-800',
}

export function Protocols() {
  const [protocols, setProtocols] = useState<Intervention[]>([])
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    getProtocols().then(setProtocols)
  }, [])

  const byTier = [1, 2, 3].map(tier => ({
    tier,
    items: protocols.filter(p => p.tier === tier),
  }))

  return (
    <div className="space-y-8 max-w-3xl">
      {byTier.map(({ tier, items }) => (
        items.length > 0 ? (
          <section key={tier}>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              {TIER_LABEL[tier]}
            </h3>
            <div className="space-y-2">
              {items.map(protocol => (
                <Card
                  key={protocol.id}
                  className="cursor-pointer"
                  onClick={() => setExpanded(expanded === protocol.id ? null : protocol.id)}
                >
                  <CardHeader className="py-3">
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-sm font-medium">{protocol.name}</CardTitle>
                      <div className="flex gap-1 shrink-0">
                        <Badge className={`text-xs ${EVIDENCE_COLOUR[protocol.evidence_grade] ?? ''}`} variant="outline">
                          {protocol.evidence_grade}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {COST_LABEL[protocol.cost_tier]}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  {expanded === protocol.id && (
                    <CardContent className="pt-0 space-y-2">
                      <p className="text-sm text-muted-foreground">{protocol.mechanism}</p>
                      {protocol.references && (
                        <div className="space-y-1">
                          <p className="text-xs font-medium">References</p>
                          {protocol.references.split('\n').filter(Boolean).map((ref, i) => (
                            <a
                              key={i}
                              href={ref}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block text-xs text-blue-600 hover:underline truncate"
                              onClick={e => e.stopPropagation()}
                            >
                              {ref}
                            </a>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </section>
        ) : null
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Build to verify no errors**

```bash
cd /home/dcb/longevity/frontend
npm run build
```

- [ ] **Step 3: Commit**

```bash
cd /home/dcb/longevity
git add frontend/src/pages/Protocols.tsx
git commit -m "feat: protocol library page with tier grouping, evidence grades, and expandable mechanism detail"
```

---

## Task 12: Manual Entry Form (BP, Mood, Symptoms)

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx` (add `ManualEntryForm` component — append to existing file)

The BP monitor has no API. Without a manual entry UI, the dashboard will never show BP data. This task adds a simple form to the Dashboard for logging any manual biomarker reading.

- [ ] **Step 1: Append ManualEntryForm to frontend/src/pages/Dashboard.tsx**

Add the following before the `export function Dashboard()` function:

```typescript
const MANUAL_METRICS = [
  { value: 'blood_pressure_systolic', label: 'BP Systolic', unit: 'mmHg' },
  { value: 'blood_pressure_diastolic', label: 'BP Diastolic', unit: 'mmHg' },
  { value: 'mood', label: 'Mood', unit: '/10' },
  { value: 'energy', label: 'Energy', unit: '/10' },
  { value: 'symptom_pain', label: 'Pain Level', unit: '/10' },
]

const ManualEntryForm = memo(function ManualEntryForm({ onSaved }: { onSaved: () => void }) {
  const [metric, setMetric] = useState(MANUAL_METRICS[0].value)
  const [value, setValue] = useState('')
  const [saving, setSaving] = useState(false)

  const selectedMetric = MANUAL_METRICS.find(m => m.value === metric)!

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const num = parseFloat(value)
    if (isNaN(num)) return
    setSaving(true)
    try {
      await createBiomarker({
        source: 'manual',
        metric,
        value: num,
        unit: selectedMetric.unit,
        recorded_at: new Date().toISOString(),
      })
      setValue('')
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Log Reading</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Metric</label>
            <select
              className="border rounded px-2 py-1 text-sm bg-background"
              value={metric}
              onChange={e => setMetric(e.target.value)}
            >
              {MANUAL_METRICS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Value ({selectedMetric.unit})</label>
            <input
              type="number"
              step="0.1"
              className="border rounded px-2 py-1 text-sm w-24 bg-background"
              value={value}
              onChange={e => setValue(e.target.value)}
              required
            />
          </div>
          <Button type="submit" size="sm" disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
})
```

- [ ] **Step 2: Add ManualEntryForm to the Dashboard render**

In `export function Dashboard()`, after the metrics grid, add:

```typescript
  const [refreshKey, setRefreshKey] = useState(0)
  // (add refreshKey to useState declarations at top of Dashboard)
  // ...existing return JSX...
  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
    {METRICS.map(m => (
      <MetricCard key={`${m.key}-${refreshKey}`} metricKey={m.key} label={m.label} unit={m.unit} color={m.color} />
    ))}
  </div>
  <ManualEntryForm onSaved={() => setRefreshKey(k => k + 1)} />
```

The full updated `Dashboard` function becomes:

```typescript
export function Dashboard() {
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  async function handleBackfill() {
    setSyncing(true)
    setSyncResult(null)
    try {
      const result = await triggerBackfill(30)
      setSyncResult(`Synced ${result.days_synced} days — ${result.inserted} new readings`)
      setRefreshKey(k => k + 1)
    } catch (e) {
      setSyncResult('Sync failed — check Garmin credentials in .env')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Biomarkers — Last 30 Days</h2>
        <div className="flex items-center gap-3">
          {syncResult ? <p className="text-sm text-muted-foreground">{syncResult}</p> : null}
          <Button variant="outline" size="sm" onClick={handleBackfill} disabled={syncing}>
            {syncing ? 'Syncing...' : 'Sync Garmin'}
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {METRICS.map(m => (
          <MetricCard key={`${m.key}-${refreshKey}`} metricKey={m.key} label={m.label} unit={m.unit} color={m.color} />
        ))}
      </div>
      <ManualEntryForm onSaved={() => setRefreshKey(k => k + 1)} />
    </div>
  )
}
```

Note: the `syncResult &&` was also changed to `syncResult ? ... : null` (ternary) per React best practices.

- [ ] **Step 3: Build to verify no TypeScript errors**

```bash
cd /home/dcb/longevity/frontend
npm run build
```

Expected: clean build.

- [ ] **Step 4: Commit**

```bash
cd /home/dcb/longevity
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat: manual entry form for BP, mood, energy, and symptom readings"
```

---

## Task 13: Systemd Services (Auto-start on Boot)

**Files:**
- Create: `/etc/systemd/system/longevity-backend.service`
- Create: `/etc/systemd/system/longevity-frontend.service`

- [ ] **Step 1: Create backend systemd service**


```bash
sudo tee /etc/systemd/system/longevity-backend.service > /dev/null << 'EOF'
[Unit]
Description=Longevity OS Backend
After=network.target

[Service]
Type=simple
User=dcb
WorkingDirectory=/home/dcb/longevity
EnvironmentFile=/home/dcb/longevity/.env
ExecStart=/home/dcb/longevity/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

- [ ] **Step 2: Build frontend for production**

```bash
cd /home/dcb/longevity/frontend
npm run build
```

- [ ] **Step 3: Create frontend systemd service (serves built static files)**

```bash
sudo tee /etc/systemd/system/longevity-frontend.service > /dev/null << 'EOF'
[Unit]
Description=Longevity OS Frontend
After=network.target

[Service]
Type=simple
User=dcb
WorkingDirectory=/home/dcb/longevity/frontend
ExecStart=/usr/bin/npx serve dist -l 3000 --single
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

- [ ] **Step 4: Enable and start both services**

```bash
sudo systemctl daemon-reload
sudo systemctl enable longevity-backend longevity-frontend
sudo systemctl start longevity-backend longevity-frontend
```

- [ ] **Step 5: Verify both are running**

```bash
sudo systemctl status longevity-backend --no-pager
sudo systemctl status longevity-frontend --no-pager
```

Expected: both show `active (running)`.

- [ ] **Step 6: Test end-to-end in browser**

Open `http://100.70.55.16:3000` in your browser.

Expected:
- Longevity OS loads with three tabs
- "Today" tab shows the Tier 1 checklist with 10 items
- "Protocols" tab shows all Tier 1 protocols grouped with evidence grades
- "Dashboard" tab shows empty metric cards with "Sync Garmin" button
- Clicking "Sync Garmin" with valid credentials populates the charts

- [ ] **Step 7: Commit**

```bash
cd /home/dcb/longevity
git add .
git commit -m "feat: Phase 1 complete — systemd auto-start for backend and frontend"
```

---

## Phase 1 Complete

At this point you have:

- **Garmin sync** running hourly in the background, backfilling up to 30 days of history on demand
- **Biomarker dashboard** with 30-day sparklines for HRV, sleep, HR, steps, weight, body fat, stress, body battery
- **Protocol checklist** with all Tier 1 interventions, compliance tracking, and progress bar
- **Protocol library** with mechanism explanations, evidence grades, and cost tiers
- **Auto-starts on boot** via systemd

**Phase 2 plan** (research synthesis + correlation analysis + blood panel import) will be written separately once Phase 1 is stable.
