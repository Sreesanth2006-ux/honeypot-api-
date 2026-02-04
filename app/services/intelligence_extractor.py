"""
Intelligence extraction service.
Extracts bank accounts, UPI IDs, phone numbers, URLs, and keywords from messages.
"""

from typing import List
from app.models import ExtractedIntelligence, Message
from app.utils.patterns import (
    BANK_ACCOUNT_PATTERN, UPI_ID_PATTERN, PHONE_PATTERN,
    URL_PATTERN, SHORTENED_URL_PATTERN, SCAM_KEYWORDS
)
from app.utils.logger import logger


class IntelligenceExtractor:
    """Service for extracting actionable intelligence from conversations."""
    
    def __init__(self):
        self.scam_keywords = [kw.lower() for kw in SCAM_KEYWORDS]
    
    def extract(self, message: Message) -> ExtractedIntelligence:
        """
        Extract intelligence from a single message.
        
        Args:
            message: The message to analyze
            
        Returns:
            ExtractedIntelligence with all detected items
        """
        text = message.text
        
        intel = ExtractedIntelligence(
            bankAccounts=self._extract_bank_accounts(text),
            upiIds=self._extract_upi_ids(text),
            phoneNumbers=self._extract_phone_numbers(text),
            phishingLinks=self._extract_urls(text),
            suspiciousKeywords=self._extract_keywords(text)
        )
        
        logger.info(
            f"Extracted intelligence: "
            f"bank_accounts={len(intel.bankAccounts)}, "
            f"upi_ids={len(intel.upiIds)}, "
            f"phones={len(intel.phoneNumbers)}, "
            f"urls={len(intel.phishingLinks)}, "
            f"keywords={len(intel.suspiciousKeywords)}"
        )
        
        return intel
    
    def extract_from_history(self, messages: List[Message]) -> ExtractedIntelligence:
        """
        Extract intelligence from entire conversation history.
        
        Args:
            messages: List of messages to analyze
            
        Returns:
            Merged ExtractedIntelligence from all messages
        """
        combined = ExtractedIntelligence()
        
        for msg in messages:
            intel = self.extract(msg)
            combined = combined.merge(intel)
        
        return combined
    
    def _extract_bank_accounts(self, text: str) -> List[str]:
        """Extract potential bank account numbers."""
        matches = BANK_ACCOUNT_PATTERN.findall(text)
        
        # Filter out likely non-account numbers
        valid_accounts = []
        for match in matches:
            # Bank accounts typically have 9-18 digits
            # Filter out obvious non-accounts (phone numbers, PINs, etc.)
            if len(match) >= 9 and len(match) <= 18:
                # Avoid phone numbers (10 digits starting with 6-9)
                if len(match) == 10 and match[0] in '6789':
                    continue
                valid_accounts.append(match)
        
        return list(set(valid_accounts))
    
    def _extract_upi_ids(self, text: str) -> List[str]:
        """Extract UPI IDs."""
        matches = UPI_ID_PATTERN.findall(text)
        
        # Validate UPI ID format
        valid_upis = []
        known_upi_handles = [
            'paytm', 'ybl', 'sbi', 'okicici', 'okhdfcbank', 
            'okaxis', 'oksbi', 'upi', 'apl', 'axisbank',
            'ibl', 'icici', 'kotak', 'indus', 'hsbc'
        ]
        
        for match in matches:
            # Check if it looks like a valid UPI ID
            if '@' in match:
                handle = match.split('@')[1].lower()
                # Accept known handles or handles that look like bank names
                if any(upi in handle for upi in known_upi_handles) or len(handle) >= 2:
                    # Exclude email addresses
                    if not any(domain in handle for domain in ['gmail', 'yahoo', 'hotmail', 'outlook', 'mail']):
                        valid_upis.append(match)
        
        return list(set(valid_upis))
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract Indian phone numbers."""
        matches = PHONE_PATTERN.findall(text)
        
        # Format consistently
        formatted = []
        for match in matches:
            # Ensure 10 digits starting with 6-9
            if len(match) == 10 and match[0] in '6789':
                formatted.append(f"+91 {match}")
        
        return list(set(formatted))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs and potential phishing links."""
        urls = URL_PATTERN.findall(text)
        shortened = SHORTENED_URL_PATTERN.findall(text)
        
        all_urls = list(set(urls))
        
        # Add shortened URLs with full protocol
        for short in shortened:
            if not short.startswith('http'):
                all_urls.append(f"https://{short}")
            else:
                all_urls.append(short)
        
        return list(set(all_urls))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords found in the text."""
        text_lower = text.lower()
        found = []
        
        for keyword in self.scam_keywords:
            if keyword in text_lower:
                found.append(keyword)
        
        return list(set(found))


# Global instance
intelligence_extractor = IntelligenceExtractor()
