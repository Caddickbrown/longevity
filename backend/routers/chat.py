from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import Conversation
from backend.schemas import ConversationMessageOut
from backend.services.persona import build_persona_context

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/", response_model=ConversationMessageOut)
def send_message(payload: ChatRequest, db: Session = Depends(get_db)):
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    import anthropic

    # Build persona system prompt
    system_prompt = build_persona_context(db)

    # Load last 20 turns as history
    history = db.execute(
        select(Conversation).order_by(Conversation.created_at.desc()).limit(20)
    ).scalars().all()
    messages = [{"role": m.role, "content": m.content} for m in reversed(history)]
    messages.append({"role": "user", "content": payload.message})

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
        )
        reply = response.content[0].text
    except anthropic.APIError as e:
        raise HTTPException(status_code=503, detail=f"Claude API error: {e}")

    # Store both turns
    db.add(Conversation(role="user", content=payload.message))
    assistant_msg = Conversation(role="assistant", content=reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg


@router.get("/history", response_model=list[ConversationMessageOut])
def get_history(db: Session = Depends(get_db)):
    return db.execute(
        select(Conversation).order_by(Conversation.created_at.asc()).limit(50)
    ).scalars().all()


@router.delete("/history", status_code=204)
def clear_history(db: Session = Depends(get_db)):
    db.execute(Conversation.__table__.delete())
    db.commit()
