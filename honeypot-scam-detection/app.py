from flask import Flask, request, jsonify
import anthropic
import os
import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from dotenv import load_dotenv
import httpx
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', message='Core Pydantic V1')

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
API_KEY = os.environ.get("HONEYPOT_API_KEY", "your-secret-api-key-here")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Validate API key
if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-anthropic-api-key-here":
    raise ValueError("ANTHROPIC_API_KEY not set in .env file!")

# Initialize Anthropic client (Python 3.14 compatible)
print("Initializing Anthropic client...")
custom_http_client = httpx.Client(
    timeout=httpx.Timeout(60.0, connect=5.0),
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    follow_redirects=True,
)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    http_client=custom_http_client,
    max_retries=2,
)
print("✓ Anthropic client initialized successfully")

# Session storage
sessions = {}

class ScamIntelligence:
    def __init__(self):
        self.bank_accounts = []
        self.upi_ids = []
        self.phishing_links = []
        self.phone_numbers = []
        self.suspicious_keywords = []
    
    def to_dict(self):
        return {
            "bankAccounts": self.bank_accounts,
            "upiIds": self.upi_ids,
            "phishingLinks": self.phishing_links,
            "phoneNumbers": self.phone_numbers,
            "suspiciousKeywords": self.suspicious_keywords
        }

class SessionData:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.scam_detected = False
        self.messages_exchanged = 0
        self.intelligence = ScamIntelligence()
        self.agent_notes = ""
        self.conversation_complete = False
        self.scam_confidence = 0.0

def extract_intelligence(text: str, intelligence: ScamIntelligence):
    """Extract scam-related intelligence from text"""
    
    # Extract bank account numbers
    bank_patterns = [
        r'\b\d{9,18}\b',
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    ]
    for pattern in bank_patterns:
        matches = re.findall(pattern, text)
        intelligence.bank_accounts.extend([m for m in matches if m not in intelligence.bank_accounts])
    
    # Extract UPI IDs
    upi_pattern = r'\b[\w\.\-]+@[\w]+\b'
    upi_matches = re.findall(upi_pattern, text)
    intelligence.upi_ids.extend([m for m in upi_matches if m not in intelligence.upi_ids and '@' in m])
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    url_matches = re.findall(url_pattern, text)
    intelligence.phishing_links.extend([m for m in url_matches if m not in intelligence.phishing_links])
    
    # Extract phone numbers
    phone_patterns = [
        r'\+91[\s-]?\d{10}',
        r'\b\d{10}\b',
        r'\+\d{1,3}[\s-]?\d{6,14}'
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        intelligence.phone_numbers.extend([m for m in matches if m not in intelligence.phone_numbers])
    
    # Extract suspicious keywords
    suspicious_terms = [
        'urgent', 'verify', 'account blocked', 'suspended', 'immediate',
        'confirm', 'OTP', 'password', 'PIN', 'CVV', 'card details',
        'bank details', 'click here', 'limited time', 'act now',
        'verify account', 'update KYC', 'deactivated', 'expire'
    ]
    
    text_lower = text.lower()
    for term in suspicious_terms:
        if term.lower() in text_lower and term not in intelligence.suspicious_keywords:
            intelligence.suspicious_keywords.append(term)

def detect_scam_intent(message: str, conversation_history: List[Dict]) -> tuple:
    """Detect if a message has scam intent using Claude"""
    
    context = ""
    if conversation_history:
        context = "Previous conversation:\n"
        for msg in conversation_history[-5:]:
            context += f"{msg['sender']}: {msg['text']}\n"
    
    context += f"\nNew message from sender: {message}"
    
    prompt = f"""You are a scam detection expert. Analyze the following message and conversation to determine if it's a scam attempt.

{context}

Analyze for common scam indicators:
- Urgency and pressure tactics
- Requests for sensitive information (OTP, PIN, passwords, bank details)
- Threats (account suspension, legal action)
- Impersonation of banks, government, or legitimate services
- Phishing links or suspicious URLs
- Promises of prizes, refunds, or money
- Poor grammar or suspicious language patterns

Respond in JSON format:
{{
    "is_scam": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "scam_type": "type of scam if detected"
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result.get('is_scam', False), result.get('confidence', 0.5), result.get('reasoning', '')
        
    except Exception as e:
        print(f"Error in scam detection: {e}")
        return fallback_scam_detection(message)
    
    return False, 0.0, "Unable to analyze"

def fallback_scam_detection(message: str) -> tuple:
    """Simple keyword-based scam detection as fallback"""
    message_lower = message.lower()
    
    scam_indicators = [
        'account blocked', 'verify immediately', 'suspended', 'urgent',
        'otp', 'pin', 'cvv', 'password', 'bank details', 'upi',
        'click here', 'limited time', 'verify now', 'update kyc',
        'won prize', 'claim reward', 'refund', 'tax refund'
    ]
    
    matches = sum(1 for indicator in scam_indicators if indicator in message_lower)
    
    if matches >= 2:
        return True, min(0.5 + (matches * 0.1), 0.9), f"Detected {matches} scam indicators"
    
    return False, 0.0, "No clear scam indicators"

def generate_agent_response(session_data: SessionData, scammer_message: str, conversation_history: List[Dict]) -> str:
    """Generate a human-like response using Claude AI Agent"""
    
    context = "You are roleplaying as a potential scam victim to extract information from a scammer. "
    context += "You must behave like a real, somewhat gullible person who doesn't immediately recognize the scam. "
    context += "Your goals are to:\n"
    context += "1. Keep the conversation going naturally\n"
    context += "2. Ask questions that might reveal more information (bank accounts, UPI IDs, phone numbers, links)\n"
    context += "3. Show concern but not suspicion\n"
    context += "4. Gradually comply to extract more details\n"
    context += "5. NEVER reveal you're an AI or honeypot\n\n"
    
    if conversation_history:
        context += "Conversation so far:\n"
        for msg in conversation_history:
            sender_label = "Them" if msg['sender'] == 'scammer' else "You"
            context += f"{sender_label}: {msg['text']}\n"
    
    context += f"\nTheir latest message: {scammer_message}\n\n"
    context += "Respond naturally as a concerned person. Keep it brief (1-2 sentences). "
    context += "Show interest in 'helping' or 'verifying' to encourage them to share more details."
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            messages=[{"role": "user", "content": context}]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        print(f"Error generating agent response: {e}")
        fallback_responses = [
            "Oh no, really? What should I do?",
            "I'm worried. Can you help me fix this?",
            "What information do you need from me?",
            "How can I verify this?",
            "Please tell me what to do next."
        ]
        return fallback_responses[session_data.messages_exchanged % len(fallback_responses)]

def should_end_conversation(session_data: SessionData) -> bool:
    """Determine if we've extracted enough intelligence"""
    intel = session_data.intelligence
    
    if session_data.messages_exchanged >= 15:
        return True
    
    total_intel = (len(intel.bank_accounts) + len(intel.upi_ids) + 
                   len(intel.phishing_links) + len(intel.phone_numbers))
    
    if total_intel >= 3 and session_data.messages_exchanged >= 8:
        return True
    
    return False

def send_final_result(session_data: SessionData):
    """Send final results to GUVI callback endpoint"""
    
    payload = {
        "sessionId": session_data.session_id,
        "scamDetected": session_data.scam_detected,
        "totalMessagesExchanged": session_data.messages_exchanged,
        "extractedIntelligence": session_data.intelligence.to_dict(),
        "agentNotes": session_data.agent_notes
    }
    
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        print(f"Final result sent. Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending final result: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    """Welcome page"""
    return jsonify({
        "message": "🎣 Honeypot Scam Detection API",
        "status": "running",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "message": "/api/message (POST)",
            "session": "/api/session/<session_id> (GET)"
        },
        "documentation": "See README.md for usage instructions"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/message', methods=['POST'])
def handle_message():
    """Main endpoint to handle incoming messages"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        
        session_id = data.get('sessionId')
        message = data.get('message', {})
        conversation_history = data.get('conversationHistory', [])
        
        sender = message.get('sender')
        text = message.get('text')
        
        if not session_id or not text:
            return jsonify({"error": "Missing required fields"}), 400
        
        if session_id not in sessions:
            sessions[session_id] = SessionData(session_id)
        
        session_data = sessions[session_id]
        session_data.messages_exchanged += 1
        
        if sender == 'scammer':
            extract_intelligence(text, session_data.intelligence)
        
        if not session_data.scam_detected:
            is_scam, confidence, reasoning = detect_scam_intent(text, conversation_history)
            
            if is_scam and confidence > 0.6:
                session_data.scam_detected = True
                session_data.scam_confidence = confidence
                session_data.agent_notes = f"Scam detected with {confidence:.0%} confidence. {reasoning}"
            
            if not is_scam or confidence < 0.4:
                return jsonify({
                    "status": "success",
                    "reply": "Thank you for the information. I'll look into this."
                })
        
        agent_reply = generate_agent_response(session_data, text, conversation_history)
        
        if should_end_conversation(session_data) and not session_data.conversation_complete:
            session_data.conversation_complete = True
            
            intel = session_data.intelligence
            summary = f"Extracted: {len(intel.bank_accounts)} bank accounts, "
            summary += f"{len(intel.upi_ids)} UPI IDs, "
            summary += f"{len(intel.phishing_links)} phishing links, "
            summary += f"{len(intel.phone_numbers)} phone numbers. "
            summary += f"Keywords: {', '.join(intel.suspicious_keywords[:5])}"
            
            if session_data.agent_notes:
                session_data.agent_notes += f". {summary}"
            else:
                session_data.agent_notes = summary
            
            send_final_result(session_data)
            
            agent_reply = "I need to check with my family first. I'll get back to you."
        
        return jsonify({
            "status": "success",
            "reply": agent_reply
        })
        
    except Exception as e:
        print(f"Error handling message: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Debug endpoint to check session information"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session_data = sessions[session_id]
    
    return jsonify({
        "sessionId": session_id,
        "scamDetected": session_data.scam_detected,
        "confidence": session_data.scam_confidence,
        "messagesExchanged": session_data.messages_exchanged,
        "conversationComplete": session_data.conversation_complete,
        "extractedIntelligence": session_data.intelligence.to_dict(),
        "agentNotes": session_data.agent_notes
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)