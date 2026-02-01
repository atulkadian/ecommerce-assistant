import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import json
import asyncio
import logging
from typing import List
from app.schemas import (
    ChatRequest, ChatResponse, ConversationCreate, 
    ConversationResponse, ConversationDetail
)
from app.agent import agent
from app.database import get_db, init_db, Conversation, ChatMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="E-Commerce Shopping Assistant API",
    description="AI-powered shopping assistant with streaming responses",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://chat.atulkadian.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "E-Commerce Shopping Assistant API",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """Stream AI responses in real-time using Server-Sent Events."""
    async def event_generator():
        try:
            # Get or create conversation
            conversation = None
            if request.conversation_id:
                conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
            else:
                # Create new conversation with first message as title (truncated)
                title = request.message[:50] + "..." if len(request.message) > 50 else request.message
                conversation = Conversation(title=title)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Convert conversation history to internal format
            history = []
            if request.conversation_history:
                history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
            
            # Stream response and collect full response
            full_response = ""
            async for chunk in agent.astream(request.message, history):
                if chunk:
                    full_response += chunk
                    yield {
                        "event": "message",
                        "data": json.dumps({"content": chunk, "done": False})
                    }
                    await asyncio.sleep(0.01)
            
            # Save messages to database if conversation exists
            if conversation:
                db.add(ChatMessage(conversation_id=conversation.id, role="user", content=request.message))
                db.add(ChatMessage(conversation_id=conversation.id, role="assistant", content=full_response))
                db.commit()
            
            # Send completion signal with conversation_id
            yield {
                "event": "message",
                "data": json.dumps({"content": "", "done": True, "conversation_id": conversation.id})
            }
            
        except Exception as e:
            logger.error(f"Error in event generator: {str(e)}", exc_info=True)
            
            """Detect specific error types for better user feedback"""
            error_message = str(e)
            error_type = "error"
            
            if "quota" in error_message.lower() or "rate limit" in error_message.lower() or "429" in error_message:
                error_type = "quota_error"
                error_message = "API quota exceeded. Please try again later or check your API key limits."
            elif "api key" in error_message.lower() or "401" in error_message or "403" in error_message:
                error_type = "auth_error"
                error_message = "Invalid API key or authentication failed."
            
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": error_message,
                    "type": error_type
                })
            }
    
    return EventSourceResponse(event_generator())


@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(conv: ConversationCreate, db: Session = Depends(get_db)):
    conversation = Conversation(title=conv.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@app.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        history = []
        if request.conversation_history:
            history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
        
        """ Collect all response chunks """
        full_response = ""
        async for chunk in agent.astream(request.message, history):
            full_response += chunk
        
        return ChatResponse(response=full_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
