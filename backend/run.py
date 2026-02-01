"""
E-Commerce Shopping Assistant - Backend
Main entry point for running the application
"""

if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
