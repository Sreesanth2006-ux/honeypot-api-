"""
Configuration module for the Agentic Honeypot API.
Loads environment variables and provides settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Authentication
    api_key: str = os.getenv("API_KEY", "honeypot-secret-key")
    
    # OpenAI API Key
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Callback URL for final results
    callback_url: str = os.getenv(
        "CALLBACK_URL", 
        "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    )
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Server Settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Session Management
    min_messages_for_callback: int = 8
    max_messages_for_callback: int = 15
    
    # Scam Detection
    scam_threshold: int = 40  # Score threshold for flagging as scam
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
