"""
Application runner script.
Use this to run the API server locally.
"""

import uvicorn
from app.config import settings


if __name__ == "__main__":
    print("🍯 Starting Agentic Honeypot API...")
    print(f"   Host: {settings.host}")
    print(f"   Port: {settings.port}")
    print(f"   Log Level: {settings.log_level}")
    print()
    print("📚 API Documentation: http://localhost:{}/docs".format(settings.port))
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enable auto-reload for development
        log_level=settings.log_level.lower()
    )
