"""
AI Agent service.
Uses OpenAI GPT-4 to generate human-like responses that engage scammers.
"""

import random
from typing import List, Optional
from openai import OpenAI
from app.config import settings
from app.models import Message, SessionData
from app.utils.logger import logger


class AIAgent:
    """AI agent for engaging scammers with human-like responses."""
    
    SYSTEM_PROMPT = """You are playing the role of an elderly Indian person (around 55-65 years old) who is not very tech-savvy but trying to learn. You've just received what appears to be a suspicious message. You are somewhat worried but also naturally skeptical.

Your personality traits:
- Slightly confused about technology and digital payments
- Cooperative but hesitant to share sensitive information
- Asks many clarifying questions
- Shows concern about the situation
- Sometimes makes typing mistakes (like "probem" instead of "problem", "acconut" for "account")
- Uses Indian English expressions occasionally ("kindly", "please do the needful", "what is the matter")
- Expresses doubt naturally ("Are you sure?", "This seems unusual", "But my son told me to never share OTP")
- Takes time to "understand" what's being asked

Your goals (but never reveal these):
1. Keep the conversation going naturally
2. Get the scammer to reveal more details about their scheme
3. Try to get them to share their payment details (bank account, UPI ID, phone number)
4. Never actually share real OTPs, passwords, or complete personal details
5. If they give you a link or phone number, ask about it to confirm

Response guidelines:
- Keep responses short (1-3 sentences typically)
- Show genuine concern about your "account" or "problem"
- Ask questions like: "What exactly will happen?", "Can you explain in simple words?", "Which bank are you calling from?"
- Occasionally mention family members: "Let me ask my son first", "My daughter handles these things"
- Express confusion about technical terms
- If they ask for OTP, stall: "OTP? You mean the number that comes on phone?", "Wait, it's loading..."
- Sometimes agree partially but ask for more details first

NEVER:
- Immediately comply with requests for OTP, password, or money transfer
- Reveal that you are a bot or that you know it's a scam
- Be aggressive or accusatory
- Use perfect grammar/spelling all the time
- Give long, formal responses"""

    TYPO_WORDS = {
        "problem": ["probem", "problm", "probelm"],
        "account": ["acconut", "accont", "acount"],
        "transfer": ["tranfer", "trasnfer", "trasfer"],
        "payment": ["payemnt", "paymnt", "paymet"],
        "please": ["plese", "pls", "plz"],
        "understand": ["understnad", "undrestand", "undrstand"],
        "message": ["messge", "mesage", "msg"],
        "verification": ["verfication", "verifcation", "verificaton"],
        "immediately": ["immediatly", "immedately", "immidiately"],
    }
    
    HESITATION_PHRASES = [
        "Hmm...", "Wait...", "Let me think...", "But...",
        "I'm not sure...", "Actually...", "One moment...",
        "Let me see...", "Okay but..."
    ]
    
    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def generate_response(
        self,
        current_message: Message,
        session: SessionData
    ) -> str:
        """
        Generate a human-like response to engage the scammer.
        
        Args:
            current_message: The scammer's latest message
            session: Current session data with history
            
        Returns:
            AI-generated response string
        """
        if not self.client:
            return self._generate_fallback_response(current_message, session)
        
        try:
            # Build conversation history for OpenAI
            messages = self._build_messages(current_message, session)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=150,
                messages=messages
            )
            
            reply = response.choices[0].message.content
            
            # Add human-like variations
            reply = self._add_human_touches(reply)
            
            logger.info(f"Generated AI response: {reply[:50]}...")
            return reply
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_fallback_response(current_message, session)
    
    def _build_messages(
        self,
        current_message: Message,
        session: SessionData
    ) -> List[dict]:
        """Build message list for OpenAI API."""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in session.conversation_history[-10:]:  # Last 10 messages
            role = "assistant" if msg.sender == "agent" else "user"
            messages.append({
                "role": role,
                "content": msg.text
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message.text
        })
        
        return messages
    
    def _add_human_touches(self, text: str) -> str:
        """Add typos, hesitation, and human-like variations."""
        # Randomly add hesitation at start (20% chance)
        if random.random() < 0.2:
            text = random.choice(self.HESITATION_PHRASES) + " " + text
        
        # Randomly add typos (15% chance per eligible word)
        words = text.split()
        for i, word in enumerate(words):
            lower_word = word.lower().strip('.,!?')
            if lower_word in self.TYPO_WORDS and random.random() < 0.15:
                typo = random.choice(self.TYPO_WORDS[lower_word])
                words[i] = word.replace(lower_word, typo)
        
        return ' '.join(words)
    
    def _generate_fallback_response(
        self,
        current_message: Message,
        session: SessionData
    ) -> str:
        """Generate a response when OpenAI API is unavailable."""
        text = current_message.text.lower()
        msg_count = session.message_count
        
        # Response templates based on message content and stage
        if msg_count <= 2:
            # Early stage - show concern and ask questions
            responses = [
                "What? My account has problem? What happened exactly?",
                "Oh no, is there some issue with my bank account? Please explain simply.",
                "What do you mean? I didn't do anything wrong. What is the matter?",
                "Hello, I don't understand. Can you please explain what is happening?",
            ]
        elif any(kw in text for kw in ['otp', 'code', 'password', 'pin']):
            # OTP/Password requests - stall
            responses = [
                "OTP? You mean the number that comes on phone? Wait, let me check...",
                "My son told me to never share these codes. Why do you need it?",
                "But the message says not to share OTP with anyone. Are you sure this is safe?",
                "Wait wait, the OTP is coming. Actually, can you tell me your name and employee ID first?",
                "I am little confused. Which department are you from exactly?",
            ]
        elif any(kw in text for kw in ['transfer', 'send', 'pay', 'upi', 'money']):
            # Payment requests - get their details
            responses = [
                "Okay, but where should I send the money? What is your UPI ID?",
                "I can transfer but what account number should I use? Please tell me slowly.",
                "My son does all my transfers. Should I give him your number to call?",
                "I am confused with all this. Can you give me a number where I can call you?",
                "Transfer to where? Please give me the account details clearly.",
            ]
        elif any(kw in text for kw in ['link', 'click', 'download', 'app']):
            # Link/App requests - ask questions
            responses = [
                "I don't know how to click links. Can you guide me step by step?",
                "My phone is very old, sometimes links don't work. What is this link for?",
                "Download app? What is the name? Maybe my son can help me install it.",
                "Is this link safe? My grandson said to be careful with clicking links.",
            ]
        elif any(kw in text for kw in ['blocked', 'suspended', 'freeze', 'closed']):
            # Threat responses - show worry
            responses = [
                "Blocked? But I just checked my balance yesterday! What happened?",
                "Oh no no, please don't block it. All my pension money is there!",
                "This is very worrying. Should I go to the bank branch directly?",
                "Suspended? But why? I didn't do anything illegal. Please help me sir.",
            ]
        else:
            # Generic responses
            responses = [
                "I am not understanding completely. Can you explain in simple words?",
                "Okay, but what do I need to do exactly? Tell me step by step.",
                "Actually, let me note down everything. What should I do first?",
                "Is this really from the bank? How can I verify?",
                "My wife is asking who is calling. What should I tell her?",
            ]
        
        response = random.choice(responses)
        return self._add_human_touches(response)


# Global instance
ai_agent = AIAgent()
