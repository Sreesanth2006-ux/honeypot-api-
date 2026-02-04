"""
Regex patterns for intelligence extraction.
"""

import re
from typing import List, Pattern

# =============================================================================
# BANK ACCOUNT PATTERNS
# =============================================================================
# Indian bank account numbers: 9-18 digits
BANK_ACCOUNT_PATTERN: Pattern = re.compile(
    r'\b(\d{9,18})\b',
    re.IGNORECASE
)

# =============================================================================
# UPI ID PATTERNS
# =============================================================================
# Format: username@bankname (e.g., user@paytm, name@ybl, john@sbi)
UPI_ID_PATTERN: Pattern = re.compile(
    r'\b([a-zA-Z0-9._-]+@[a-zA-Z]{2,})\b',
    re.IGNORECASE
)

# =============================================================================
# PHONE NUMBER PATTERNS
# =============================================================================
# Indian phone numbers: +91, 91, or direct 10 digits
PHONE_PATTERN: Pattern = re.compile(
    r'(?:\+91[\s-]?|91[\s-]?)?([6-9]\d{9})\b',
    re.IGNORECASE
)

# =============================================================================
# URL/PHISHING LINK PATTERNS
# =============================================================================
URL_PATTERN: Pattern = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+',
    re.IGNORECASE
)

# Suspicious shortened URLs
SHORTENED_URL_PATTERN: Pattern = re.compile(
    r'\b(bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|buff\.ly|ow\.ly|rebrand\.ly)/\S+',
    re.IGNORECASE
)

# =============================================================================
# SUSPICIOUS KEYWORDS
# =============================================================================
SCAM_KEYWORDS: List[str] = [
    # Urgency
    "urgent", "immediately", "right now", "within 24 hours", "act fast",
    "hurry", "limited time", "expires today", "last chance",
    
    # Account related
    "blocked", "suspended", "verify", "verification", "update",
    "expired", "deactivated", "locked", "restricted",
    
    # Banking/Financial
    "otp", "bank", "upi", "account", "transaction", "transfer",
    "payment", "refund", "credit", "debit", "balance",
    
    # Scam indicators
    "prize", "lottery", "winner", "won", "congratulations", "selected",
    "lucky", "reward", "cash prize", "free gift",
    
    # KYC/Documentation
    "kyc", "pan card", "aadhar", "aadhaar", "documents", "identity",
    
    # Government/Authority
    "rbi", "income tax", "customs", "police", "court", "legal",
    "government", "ministry", "department",
    
    # Threats
    "arrest", "fine", "penalty", "legal action", "case filed",
    "fir", "complaint", "investigate", "fraud",
    
    # Instructions
    "click here", "click the link", "download", "install",
    "share otp", "send money", "pay now"
]

# =============================================================================
# IMPERSONATION KEYWORDS
# =============================================================================
BANK_NAMES: List[str] = [
    "sbi", "state bank", "hdfc", "icici", "axis", "kotak",
    "pnb", "punjab national", "bob", "bank of baroda",
    "canara", "union bank", "idbi", "yes bank", "indusind",
    "paytm", "phonepe", "gpay", "google pay", "amazon pay"
]

AUTHORITY_NAMES: List[str] = [
    "rbi", "reserve bank", "income tax", "it department",
    "customs", "police", "cyber cell", "cbi", "ed",
    "enforcement directorate", "sebi", "trai",
    "telecom", "airtel", "jio", "vodafone", "bsnl"
]

# =============================================================================
# THREAT INDICATORS
# =============================================================================
THREAT_KEYWORDS: List[str] = [
    "blocked", "suspended", "arrest", "legal action",
    "case filed", "fir", "complaint", "penalty", "fine",
    "terminate", "cancel", "disconnect", "seize"
]

# =============================================================================
# URGENCY INDICATORS
# =============================================================================
URGENCY_KEYWORDS: List[str] = [
    "urgent", "immediately", "right now", "within 24 hours",
    "within 2 hours", "today only", "expires", "last warning",
    "final notice", "act fast", "hurry", "don't delay"
]
