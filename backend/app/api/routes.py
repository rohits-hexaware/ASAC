"""Chat endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.models import get_db

from app.api.chat import handle_chat, get_chat_history
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()



@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return await handle_chat(request, db)


@router.get("/chat/{analysis_id}")
async def get_history_chat(analysis_id: str, db: Session = Depends(get_db)):
    return await get_chat_history(analysis_id, db)


