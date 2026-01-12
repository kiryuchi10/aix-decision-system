from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """AI Agent Chat Mode (stub/placeholder)"""
    # TODO: Implement actual LLM integration and tool routing
    return ChatResponse(
        response=f"Chat functionality coming soon. You said: {request.message}",
        status="placeholder"
    )
