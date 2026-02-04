"""
Scam detection router.
Handles the /api/scam-detection endpoint.
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from app.auth import verify_api_key
from app.models import (
    ScamDetectionRequest, 
    ScamDetectionResponse,
    Message
)
from app.services.scam_detector import scam_detector
from app.services.intelligence_extractor import intelligence_extractor
from app.services.session_manager import session_manager
from app.services.ai_agent import ai_agent
from app.services.callback_service import callback_service
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["scam-detection"])


@router.post("/scam-detection", response_model=ScamDetectionResponse)
async def detect_scam(
    request: ScamDetectionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> ScamDetectionResponse:
    """
    Analyze incoming message for scam patterns and generate an engaging response.
    
    This endpoint:
    1. Analyzes the message for scam indicators
    2. Extracts intelligence (bank accounts, UPI IDs, phone numbers, URLs)
    3. Generates a human-like response to engage the sender
    4. Tracks conversation state for the session
    5. Triggers final callback when sufficient engagement is reached
    
    Args:
        request: ScamDetectionRequest with message and session info
        background_tasks: FastAPI background tasks for async callback
        api_key: Validated API key from header
        
    Returns:
        ScamDetectionResponse with status and AI-generated reply
    """
    session_id = request.sessionId
    message = request.message
    history = request.conversationHistory
    
    logger.info(f"Processing message for session {session_id}: {message.text[:50]}...")
    
    # Step 1: Detect scam patterns
    detection_result = scam_detector.analyze(message, history)
    
    # Step 2: Extract intelligence
    intel = intelligence_extractor.extract(message)
    
    # Also extract from history if provided
    if history:
        history_intel = intelligence_extractor.extract_from_history(history)
        intel = intel.merge(history_intel)
    
    # Step 3: Update session
    tactics = []
    if detection_result.impersonation_indicators:
        tactics.extend(detection_result.impersonation_indicators)
    if detection_result.threat_indicators:
        tactics.append("threat_detected")
    if detection_result.urgency_indicators:
        tactics.append("urgency_tactics")
    
    session = session_manager.update_session(
        session_id=session_id,
        message=message,
        intelligence=intel,
        scam_detected=detection_result.is_scam,
        scam_score=detection_result.confidence_score,
        tactics=tactics
    )
    
    # Step 4: Generate AI response
    response_text = ai_agent.generate_response(message, session)
    
    # Add agent response to session
    session_manager.add_agent_response(session_id, response_text)
    
    # Step 5: Check if we should trigger callback
    if session_manager.should_trigger_callback(session_id):
        logger.info(f"Triggering callback for session {session_id}")
        session_manager.mark_callback_sent(session_id)
        
        # Run callback in background to not block response
        background_tasks.add_task(
            callback_service.send_final_result,
            session
        )
    
    return ScamDetectionResponse(
        status="success",
        reply=response_text
    )


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get current session information (for debugging/testing).
    
    Args:
        session_id: Session identifier
        api_key: Validated API key
        
    Returns:
        Session data or 404 if not found
    """
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}
    
    return {
        "session_id": session.session_id,
        "message_count": session.message_count,
        "scam_detected": session.scam_detected,
        "scam_score": session.scam_score,
        "callback_sent": session.callback_sent,
        "extracted_intelligence": session.extracted_intelligence.model_dump(),
        "scammer_tactics": session.scammer_tactics
    }


@router.post("/trigger-callback/{session_id}")
async def manual_trigger_callback(
    session_id: str,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger the final callback for a session.
    Useful for testing or forcing early completion.
    
    Args:
        session_id: Session identifier
        background_tasks: FastAPI background tasks
        api_key: Validated API key
        
    Returns:
        Status of callback trigger
    """
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}
    
    if session.callback_sent:
        return {"error": "Callback already sent", "session_id": session_id}
    
    session_manager.mark_callback_sent(session_id)
    background_tasks.add_task(
        callback_service.send_final_result,
        session
    )
    
    return {
        "status": "callback_triggered",
        "session_id": session_id,
        "message_count": session.message_count
    }
