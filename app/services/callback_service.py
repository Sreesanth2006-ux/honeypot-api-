"""
Callback service.
Handles posting final results to the hackathon API.
"""

import httpx
import asyncio
from typing import Optional
from app.models import CallbackPayload, SessionData
from app.config import settings
from app.utils.logger import logger


class CallbackService:
    """Service for sending final results to the hackathon API."""
    
    def __init__(self):
        self.callback_url = settings.callback_url
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    async def send_final_result(self, session: SessionData) -> bool:
        """
        Send final callback with extracted intelligence.
        
        Args:
            session: Session data with all extracted intelligence
            
        Returns:
            True if callback was successful, False otherwise
        """
        payload = self._build_payload(session)
        
        logger.info(
            f"Sending callback for session {session.session_id}: "
            f"messages={payload.totalMessagesExchanged}, "
            f"scam_detected={payload.scamDetected}"
        )
        
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.callback_url,
                        json=payload.model_dump(),
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code in [200, 201, 202]:
                        logger.info(
                            f"Callback successful for session {session.session_id} "
                            f"(attempt {attempt}): status={response.status_code}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Callback failed for session {session.session_id} "
                            f"(attempt {attempt}): status={response.status_code}, "
                            f"response={response.text[:200]}"
                        )
                        
            except httpx.TimeoutException:
                logger.warning(
                    f"Callback timeout for session {session.session_id} "
                    f"(attempt {attempt})"
                )
            except Exception as e:
                logger.error(
                    f"Callback error for session {session.session_id} "
                    f"(attempt {attempt}): {e}"
                )
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * attempt)
        
        logger.error(
            f"All callback attempts failed for session {session.session_id}"
        )
        return False
    
    def _build_payload(self, session: SessionData) -> CallbackPayload:
        """Build the callback payload from session data."""
        # Generate agent notes summarizing the interaction
        agent_notes = self._generate_agent_notes(session)
        
        return CallbackPayload(
            sessionId=session.session_id,
            scamDetected=session.scam_detected,
            totalMessagesExchanged=session.message_count,
            extractedIntelligence=session.extracted_intelligence,
            agentNotes=agent_notes
        )
    
    def _generate_agent_notes(self, session: SessionData) -> str:
        """Generate a summary of scammer behavior and tactics."""
        notes_parts = []
        
        # Detected tactics
        if session.scammer_tactics:
            tactics_str = ", ".join(session.scammer_tactics[:10])  # Limit to 10
            notes_parts.append(f"Detected tactics: {tactics_str}")
        
        # Scam score
        notes_parts.append(f"Scam confidence score: {session.scam_score}/100")
        
        # Intelligence summary
        intel = session.extracted_intelligence
        intel_items = []
        if intel.bankAccounts:
            intel_items.append(f"{len(intel.bankAccounts)} bank account(s)")
        if intel.upiIds:
            intel_items.append(f"{len(intel.upiIds)} UPI ID(s)")
        if intel.phoneNumbers:
            intel_items.append(f"{len(intel.phoneNumbers)} phone number(s)")
        if intel.phishingLinks:
            intel_items.append(f"{len(intel.phishingLinks)} URL(s)")
        
        if intel_items:
            notes_parts.append(f"Extracted: {', '.join(intel_items)}")
        
        # Conversation summary
        notes_parts.append(
            f"Engaged over {session.message_count} messages from "
            f"{session.created_at.strftime('%Y-%m-%d %H:%M')} UTC"
        )
        
        return ". ".join(notes_parts)


# Global instance
callback_service = CallbackService()
