import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import logging
from app.schemas import ChatRequest, ChatResponse
from app.agent import agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="E-Commerce Shopping Assistant API",
    description="AI-powered shopping assistant with streaming responses",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "E-Commerce Shopping Assistant API",
        "status": "active",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream AI responses in real-time using Server-Sent Events."""
    async def event_generator():
        try:
            """Convert conversation history to internal format"""
            history = []
            if request.conversation_history:
                history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
            
            logger.info(f"Processing message with {len(history)} history items")
            
            """ Stream response chunks from the agent """
            async for chunk in agent.astream(request.message, history):
                if chunk:
                    yield {
                        "event": "message",
                        "data": json.dumps({"content": chunk, "done": False})
                    }
                    await asyncio.sleep(0.01)  # Small delay for smoother streaming
            
            """Send completion signal"""
            yield {
                "event": "message",
                "data": json.dumps({"content": "", "done": True})
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
