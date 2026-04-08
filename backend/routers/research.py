from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Intervention, ResearchDigest
from backend.schemas import ResearchDigestOut
from backend.services.research_fetcher import FetchError, fetch_research
from backend.services.research_synthesiser import SynthesisError, synthesise

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/", response_model=list[ResearchDigestOut])
def list_digests(db: Session = Depends(get_db)):
    stmt = select(ResearchDigest).order_by(ResearchDigest.generated_at.desc()).limit(10)
    return db.execute(stmt).scalars().all()


@router.get("/{digest_id}", response_model=ResearchDigestOut)
def get_digest(digest_id: int, db: Session = Depends(get_db)):
    digest = db.get(ResearchDigest, digest_id)
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    return digest


@router.post("/generate", response_model=ResearchDigestOut, status_code=201)
def generate_digest(db: Session = Depends(get_db)):
    # Get active protocol names for the synthesis prompt
    protocols = db.execute(select(Intervention.name)).scalars().all()

    try:
        articles = fetch_research()
    except FetchError as e:
        raise HTTPException(status_code=503, detail=f"Research fetch failed: {e}")

    try:
        digest_data = synthesise(articles, list(protocols))
    except SynthesisError as e:
        raise HTTPException(status_code=503, detail=str(e))

    digest = ResearchDigest(**digest_data)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest
