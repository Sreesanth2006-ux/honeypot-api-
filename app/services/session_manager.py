"""
Session management service.
Tracks conversation state and extracted intelligence per session.
"""

from typing import Dict, Optional
from datetime import datetime
from app.models import SessionData, Message, ExtractedIntelligence
from app.config import settings
from app.utils.logger import logger


class SessionManager:
    """In-memory session storage and management."""
    
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}
    
    def get_or_create_session(self, session_id: str) -> SessionData:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            SessionData for the session
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionData(
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            logger.info(f"Created new session: {session_id}")
        
        return self._sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session if it exists."""
        return self._sessions.get(session_id)
    
    def update_session(
        self,
        session_id: str,
        message: Message,
        intelligence: ExtractedIntelligence,
        scam_detected: bool,
        scam_score: int,
        tactics: list = None
    ) -> SessionData:
        """
        Update session with new message and extracted intelligence.
        
        Args:
            session_id: Session identifier
            message: New message to add
            intelligence: Extracted intelligence from this message
            scam_detected: Whether scam was detected
            scam_score: Scam confidence score
            tactics: Detected scammer tactics
            
        Returns:
            Updated SessionData
        """
        session = self.get_or_create_session(session_id)
        
        # Add message to history
        session.conversation_history.append(message)
        session.message_count = len(session.conversation_history)
        
        # Merge intelligence
        session.extracted_intelligence = session.extracted_intelligence.merge(intelligence)
        
        # Update scam detection
        if scam_detected:
            session.scam_detected = True
        session.scam_score = max(session.scam_score, scam_score)
        
        # Add tactics
        if tactics:
            session.scammer_tactics.extend(tactics)
            session.scammer_tactics = list(set(session.scammer_tactics))
        
        logger.info(
            f"Updated session {session_id}: "
            f"messages={session.message_count}, "
            f"scam_detected={session.scam_detected}"
        )
        
        return session
    
    def add_agent_response(self, session_id: str, response_text: str) -> SessionData:
        """
        Add agent's response to the conversation history.
        
        Args:
            session_id: Session identifier
            response_text: Agent's response
            
        Returns:
            Updated SessionData
        """
        session = self.get_or_create_session(session_id)
        
        agent_message = Message(
            sender="agent",
            text=response_text,
            timestamp=datetime.utcnow().isoformat()
        )
        session.conversation_history.append(agent_message)
        session.message_count = len(session.conversation_history)
        
        return session
    
    def should_trigger_callback(self, session_id: str) -> bool:
        """
        Determine if we should trigger the final callback.
        
        Criteria:
        1. Minimum messages reached (8+) OR
        2. Maximum messages reached (15+) OR
        3. Key intelligence extracted (payment + contact info)
        
        AND callback hasn't been sent yet.
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if session.callback_sent:
            return False
        
        if not session.scam_detected:
            return False
        
        # Check message count
        msg_count = session.message_count
        min_msgs = settings.min_messages_for_callback
        max_msgs = settings.max_messages_for_callback
        
        # Maximum reached - always trigger
        if msg_count >= max_msgs:
            logger.info(f"Session {session_id}: Max messages reached ({msg_count})")
            return True
        
        # Minimum reached with key intelligence
        if msg_count >= min_msgs:
            intel = session.extracted_intelligence
            if intel.has_key_intelligence():
                logger.info(
                    f"Session {session_id}: Min messages + key intelligence "
                    f"(msgs={msg_count}, has_intel=True)"
                )
                return True
        
        return False
    
    def mark_callback_sent(self, session_id: str) -> None:
        """Mark that callback has been sent for this session."""
        session = self.get_session(session_id)
        if session:
            session.callback_sent = True
            logger.info(f"Session {session_id}: Callback marked as sent")
    
    def get_all_sessions(self) -> Dict[str, SessionData]:
        """Get all sessions (for debugging)."""
        return self._sessions
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global instance
session_manager = SessionManager()
