import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import json
import asyncio
import logging
import os
from typing import List, Optional
from app.schemas import (
    ChatRequest, ChatResponse, ConversationCreate, 
    ConversationResponse, ConversationDetail
)
from app.agent import ShoppingAssistantAgent
from app.database import get_db, init_db, Conversation, ChatMessage
from app.vector_store import initialize_vector_store
from app.api_client import fake_store_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load auth key from environment (required)
AUTH_KEY = os.getenv("AUTH_KEY")
if not AUTH_KEY:
    raise ValueError("AUTH_KEY environment variable must be set")

def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify authentication token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if the header starts with "Bearer "
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    if token != AUTH_KEY:
        raise HTTPException(status_code=401, detail="Invalid authentication key")
    
    return True

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="E-Commerce Shopping Assistant API",
    description="AI-powered shopping assistant with streaming responses",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup():
    init_db()
    # Initialize vector store for semantic search
    try:
        logger.info("Initializing semantic search vector store...")
        products = await fake_store_api.get_products()
        initialize_vector_store(products)
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        # Continue without vector store - will fallback to keyword search

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://chat.atulkadian.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root(authenticated: bool = Depends(verify_auth)):
    return {
        "message": "E-Commerce Shopping Assistant API",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request, 
    chat_request: ChatRequest, 
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_auth)
):
    """Stream AI responses in real-time using Server-Sent Events."""
    async def event_generator():
        conversation = None
        conversation_created = False
        
        try:
            if chat_request.conversation_id:
                conversation = db.query(Conversation).filter(Conversation.id == chat_request.conversation_id).first()
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
            
            history = []
            if chat_request.conversation_history:
                history = [{"role": msg.role, "content": msg.content} for msg in chat_request.conversation_history]
            
            agent_instance = ShoppingAssistantAgent(db=db)
            
            full_response = ""
            async for chunk in agent_instance.astream(chat_request.message, history):
                if chunk:
                    # Create conversation after first chunk is received (only for new conversations)
                    if not conversation and not conversation_created:
                        title = chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
                        conversation = Conversation(title=title)
                        db.add(conversation)
                        db.commit()
                        db.refresh(conversation)
                        conversation_created = True
                    
                    full_response += chunk
                    yield {
                        "event": "message",
                        "data": json.dumps({"content": chunk, "done": False})
                    }
                    await asyncio.sleep(0.01)
            
            # Save messages to database if conversation exists
            if conversation:
                db.add(ChatMessage(conversation_id=conversation.id, role="user", content=chat_request.message))
                db.add(ChatMessage(conversation_id=conversation.id, role="assistant", content=full_response))
                db.commit()
            
            # Send completion signal with conversation_id
            yield {
                "event": "message",
                "data": json.dumps({"content": "", "done": True, "conversation_id": conversation.id if conversation else None})
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
@limiter.limit("30/minute")
def create_conversation(
    request: Request, 
    conv: ConversationCreate, 
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_auth)
):
    conversation = Conversation(title=conv.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.get("/conversations", response_model=List[ConversationResponse])
@limiter.limit("60/minute")
def list_conversations(
    request: Request, 
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_auth)
):
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@app.get("/conversations/{conversation_id}", response_model=ConversationDetail)
@limiter.limit("60/minute")
def get_conversation(
    request: Request, 
    conversation_id: int, 
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_auth)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
@limiter.limit("30/minute")
def delete_conversation(
    request: Request, 
    conversation_id: int, 
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_auth)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request, 
    chat_request: ChatRequest, 
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_auth)
):
    try:
        history = []
        if chat_request.conversation_history:
            history = [{"role": msg.role, "content": msg.content} for msg in chat_request.conversation_history]
        
        # Create agent instance with db session
        agent_instance = ShoppingAssistantAgent(db=db)
        
        """ Collect all response chunks """
        full_response = ""
        async for chunk in agent_instance.astream(chat_request.message, history):
            full_response += chunk
        
        return ChatResponse(response=full_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
