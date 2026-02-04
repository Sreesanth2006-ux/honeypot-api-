"""
Pydantic models for request/response validation.
Flexible to accept various input formats from hackathon.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Message(BaseModel):
    """Incoming message from the conversation."""
    sender: str = Field(default="scammer", description="Sender identifier")
    text: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="ISO format timestamp")


class Metadata(BaseModel):
    """Metadata about the conversation context."""
    channel: str = Field(default="sms", description="Communication channel")
    language: str = Field(default="en", description="Message language")
    locale: str = Field(default="en-IN", description="Locale for formatting")


class ScamDetectionRequest(BaseModel):
    """
    Flexible request payload for scam detection endpoint.
    Accepts various formats from hackathon tester.
    """
    # Try multiple field names for session ID
    sessionId: Optional[str] = Field(default=None, description="Session ID")
    session_id: Optional[str] = Field(default=None, description="Session ID (snake_case)")
    
    # Message can be a Message object OR just a string
    message: Optional[Union[Message, str, Dict[str, Any]]] = Field(default=None)
    text: Optional[str] = Field(default=None, description="Direct text field")
    content: Optional[str] = Field(default=None, description="Content field")
    
    # Optional conversation history
    conversationHistory: Optional[List[Message]] = Field(default_factory=list)
    conversation_history: Optional[List[Dict]] = Field(default=None)
    
    # Optional metadata
    metadata: Optional[Metadata] = Field(default_factory=Metadata)
    
    def get_session_id(self) -> str:
        """Get session ID from various possible fields."""
        return self.sessionId or self.session_id or f"session-{datetime.utcnow().timestamp()}"
    
    def get_message_text(self) -> str:
        """Extract message text from various possible fields."""
        # Direct text field
        if self.text:
            return self.text
        if self.content:
            return self.content
        
        # Message as string
        if isinstance(self.message, str):
            return self.message
        
        # Message as dict
        if isinstance(self.message, dict):
            return self.message.get("text", "") or self.message.get("content", "")
        
        # Message as Message object
        if self.message and hasattr(self.message, "text"):
            return self.message.text
        
        return ""
    
    def get_message_object(self) -> Message:
        """Get a proper Message object."""
        text = self.get_message_text()
        sender = "scammer"
        timestamp = datetime.utcnow().isoformat()
        
        if isinstance(self.message, Message):
            return self.message
        elif isinstance(self.message, dict):
            sender = self.message.get("sender", "scammer")
            timestamp = self.message.get("timestamp", timestamp)
        
        return Message(sender=sender, text=text, timestamp=timestamp)


class ScamDetectionResponse(BaseModel):
    """Response from scam detection endpoint."""
    status: str = Field(default="success", description="Response status")
    reply: str = Field(..., description="AI agent's response")


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from the conversation."""
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)
    
    def has_key_intelligence(self) -> bool:
        """Check if we have extracted key intelligence."""
        has_payment_info = bool(self.bankAccounts or self.upiIds)
        has_contact_info = bool(self.phoneNumbers or self.phishingLinks)
        return has_payment_info and has_contact_info
    
    def merge(self, other: "ExtractedIntelligence") -> "ExtractedIntelligence":
        """Merge intelligence from another extraction."""
        return ExtractedIntelligence(
            bankAccounts=list(set(self.bankAccounts + other.bankAccounts)),
            upiIds=list(set(self.upiIds + other.upiIds)),
            phishingLinks=list(set(self.phishingLinks + other.phishingLinks)),
            phoneNumbers=list(set(self.phoneNumbers + other.phoneNumbers)),
            suspiciousKeywords=list(set(self.suspiciousKeywords + other.suspiciousKeywords))
        )


class CallbackPayload(BaseModel):
    """Payload for the final callback to hackathon API."""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str = Field(
        default="", 
        description="Summary of scammer behavior and tactics observed"
    )


class SessionData(BaseModel):
    """Internal session tracking data."""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    conversation_history: List[Message] = Field(default_factory=list)
    extracted_intelligence: ExtractedIntelligence = Field(
        default_factory=ExtractedIntelligence
    )
    scam_detected: bool = False
    scam_score: int = 0
    callback_sent: bool = False
    scammer_tactics: List[str] = Field(default_factory=list)


class ScamDetectionResult(BaseModel):
    """Result from scam detection analysis."""
    is_scam: bool
    confidence_score: int  # 0-100
    detected_keywords: List[str]
    urgency_indicators: List[str]
    impersonation_indicators: List[str]
    threat_indicators: List[str]
