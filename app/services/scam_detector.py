"""
Scam detection service.
Analyzes messages to detect scam patterns and score likelihood.
"""

from typing import List, Tuple
from app.models import ScamDetectionResult, Message
from app.utils.patterns import (
    SCAM_KEYWORDS, BANK_NAMES, AUTHORITY_NAMES,
    THREAT_KEYWORDS, URGENCY_KEYWORDS
)
from app.utils.logger import logger


class ScamDetector:
    """Service for detecting scam patterns in messages."""
    
    def __init__(self):
        self.scam_keywords = [kw.lower() for kw in SCAM_KEYWORDS]
        self.bank_names = [bn.lower() for bn in BANK_NAMES]
        self.authority_names = [an.lower() for an in AUTHORITY_NAMES]
        self.threat_keywords = [tk.lower() for tk in THREAT_KEYWORDS]
        self.urgency_keywords = [uk.lower() for uk in URGENCY_KEYWORDS]
    
    def analyze(self, message: Message, history: List[Message] = None) -> ScamDetectionResult:
        """
        Analyze a message for scam indicators.
        
        Args:
            message: The message to analyze
            history: Previous messages in the conversation
            
        Returns:
            ScamDetectionResult with detection details
        """
        text = message.text.lower()
        
        # Also analyze recent history for context
        full_text = text
        if history:
            recent_history = history[-5:]  # Look at last 5 messages
            full_text += " " + " ".join([m.text.lower() for m in recent_history])
        
        # Detect various indicators
        detected_keywords = self._detect_keywords(full_text)
        urgency_indicators = self._detect_urgency(full_text)
        impersonation_indicators = self._detect_impersonation(full_text)
        threat_indicators = self._detect_threats(full_text)
        
        # Calculate confidence score
        score = self._calculate_score(
            detected_keywords,
            urgency_indicators,
            impersonation_indicators,
            threat_indicators
        )
        
        result = ScamDetectionResult(
            is_scam=score >= 40,
            confidence_score=min(score, 100),
            detected_keywords=detected_keywords,
            urgency_indicators=urgency_indicators,
            impersonation_indicators=impersonation_indicators,
            threat_indicators=threat_indicators
        )
        
        logger.info(
            f"Scam detection result: is_scam={result.is_scam}, "
            f"score={result.confidence_score}, "
            f"keywords={len(detected_keywords)}"
        )
        
        return result
    
    def _detect_keywords(self, text: str) -> List[str]:
        """Detect scam-related keywords in text."""
        found = []
        for keyword in self.scam_keywords:
            if keyword in text:
                found.append(keyword)
        return list(set(found))
    
    def _detect_urgency(self, text: str) -> List[str]:
        """Detect urgency indicators in text."""
        found = []
        for phrase in self.urgency_keywords:
            if phrase in text:
                found.append(phrase)
        return list(set(found))
    
    def _detect_impersonation(self, text: str) -> List[str]:
        """Detect impersonation of banks or authorities."""
        found = []
        for name in self.bank_names:
            if name in text:
                found.append(f"Bank: {name.upper()}")
        for name in self.authority_names:
            if name in text:
                found.append(f"Authority: {name.upper()}")
        return list(set(found))
    
    def _detect_threats(self, text: str) -> List[str]:
        """Detect threatening language."""
        found = []
        for threat in self.threat_keywords:
            if threat in text:
                found.append(threat)
        return list(set(found))
    
    def _calculate_score(
        self,
        keywords: List[str],
        urgency: List[str],
        impersonation: List[str],
        threats: List[str]
    ) -> int:
        """
        Calculate scam confidence score (0-100).
        
        Scoring:
        - Each keyword: 5 points (max 30)
        - Each urgency indicator: 10 points (max 20)
        - Each impersonation: 15 points (max 30)
        - Each threat: 10 points (max 20)
        """
        score = 0
        
        # Keywords contribute up to 30 points
        score += min(len(keywords) * 5, 30)
        
        # Urgency contributes up to 20 points
        score += min(len(urgency) * 10, 20)
        
        # Impersonation contributes up to 30 points
        score += min(len(impersonation) * 15, 30)
        
        # Threats contribute up to 20 points
        score += min(len(threats) * 10, 20)
        
        return score


# Global instance
scam_detector = ScamDetector()
