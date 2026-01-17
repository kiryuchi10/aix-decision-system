from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

from app.routers.auth import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.services.deepseek_service import deepseek_service
from app.services.db_query_service import DatabaseQueryService

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None
    include_schema: bool = False

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    sources: Optional[List[str]] = None
    query_used: Optional[str] = None

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Agent Chat with DeepSeek integration and database context
    
    The AI can:
    - Answer questions about the AiX Decision System
    - Query database schema and data
    - Provide insights on SPC, FDC, and process data
    - Help with troubleshooting and optimization
    """
    try:
        # Initialize services
        db_service = DatabaseQueryService(db)
        
        # Build context for the AI
        messages = []
        system_prompt = deepseek_service.get_system_prompt_for_aix()
        
        # Add database schema context if requested
        context_parts = []
        if request.include_schema:
            schema_summary = db_service.get_schema_summary()
            context_parts.append(f"Database Schema Summary:\n{json.dumps(schema_summary, indent=2)}")
        
        # Add recent data summary
        recent_summary = db_service.get_recent_data_summary()
        context_parts.append(f"Recent Data Summary:\n{json.dumps(recent_summary, indent=2)}")
        
        # Add user's message with context
        user_message = request.message
        if context_parts:
            user_message = f"{user_message}\n\nContext:\n" + "\n\n".join(context_parts)
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Check if message contains a query request
        query_used = None
        if any(keyword in request.message.lower() for keyword in ["query", "select", "show", "list", "get data"]):
            # Try to extract and execute a safe query
            try:
                # This is a simple extraction - in production, use more sophisticated parsing
                if "from" in request.message.lower():
                    # User might be asking for a query
                    # For now, we'll let the AI suggest queries rather than executing them directly
                    pass
            except Exception:
                pass
        
        # Call DeepSeek API
        if deepseek_service.is_configured():
            try:
                response_text = await deepseek_service.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                return ChatResponse(
                    response=response_text,
                    status="success",
                    sources=["database", "deepseek"],
                    query_used=query_used
                )
            except Exception as e:
                # Fallback to basic response if DeepSeek fails
                return ChatResponse(
                    response=f"I encountered an error connecting to the AI service: {str(e)}\n\nHowever, I can still help you with database queries. Please try asking about specific tables or data.",
                    status="partial",
                    sources=["database"]
                )
        else:
            # Fallback: Provide helpful response without AI
            return ChatResponse(
                response=f"""I'm currently running without AI capabilities. To enable full AI chat, please set the DEEPSEEK_API_KEY environment variable.

However, I can help you with:
- Database schema information (ask about tables)
- Recent data summaries
- Query suggestions

What would you like to know about the AiX Decision System database?""",
                status="no_ai",
                sources=["database"]
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )

@router.get("/schema")
async def get_schema(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get database schema information"""
    db_service = DatabaseQueryService(db)
    schema = db_service.get_schema_summary()
    return {"schema": schema}

@router.get("/table/{table_name}")
async def get_table_info(
    table_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get information about a specific table"""
    db_service = DatabaseQueryService(db)
    table_info = db_service.get_table_info(table_name)
    if not table_info:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return {"table": table_info}

@router.get("/summary")
async def get_data_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of recent data"""
    db_service = DatabaseQueryService(db)
    summary = db_service.get_recent_data_summary()
    return {"summary": summary}
