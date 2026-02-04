"""
Pydantic models for request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Incoming message from the conversation."""
    sender: str = Field(..., description="Sender identifier (e.g., 'scammer', 'user')")
    text: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO format timestamp")


class Metadata(BaseModel):
    """Metadata about the conversation context."""
    channel: str = Field(default="sms", description="Communication channel")
    language: str = Field(default="en", description="Message language")
    locale: str = Field(default="en-IN", description="Locale for formatting")


class ScamDetectionRequest(BaseModel):
    """Request payload for scam detection endpoint."""
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Current message to analyze")
    conversationHistory: List[Message] = Field(
        default_factory=list, 
        description="Previous messages in the conversation"
    )
    metadata: Metadata = Field(
        default_factory=Metadata, 
        description="Conversation metadata"
    )


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
