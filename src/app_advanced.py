"""
Advanced version with Redis session storage for production use
This version includes better session management, logging, and metrics
"""

from flask import Flask, request, jsonify
import anthropic
import os
import re
import requests
from datetime import datetime
import json
import logging
from functools import wraps

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.environ.get("HONEYPOT_API_KEY", "your-secret-api-key-here")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

# Session storage (use Redis in production)
# Example: redis_client = redis.Redis(host='localhost', port=6379, db=0)
sessions = {}

# Metrics
metrics = {
    "total_messages": 0,
    "scams_detected": 0,
    "intelligence_extracted": 0,
    "conversations_completed": 0
}

class ScamIntelligence:
    def __init__(self):
        self.bank_accounts = []
        self.upi_ids = []
        self.phishing_links = []
        self.phone_numbers = []
        self.suspicious_keywords = []
    
    def to_dict(self):
        return {
            "bankAccounts": list(set(self.bank_accounts)),
            "upiIds": list(set(self.upi_ids)),
            "phishingLinks": list(set(self.phishing_links)),
            "phoneNumbers": list(set(self.phone_numbers)),
            "suspiciousKeywords": list(set(self.suspicious_keywords))
        }
    
    def count(self):
        return (len(self.bank_accounts) + len(self.upi_ids) + 
                len(self.phishing_links) + len(self.phone_numbers))

class SessionData:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.scam_detected = False
        self.messages_exchanged = 0
        self.intelligence = ScamIntelligence()
        self.agent_notes = ""
        self.conversation_complete = False
        self.scam_confidence = 0.0
        self.created_at = datetime.utcnow()
        self.scam_type = ""

def require_api_key(f):
    """Decorator for API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if api_key != API_KEY:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def extract_intelligence(text: str, intelligence: ScamIntelligence):
    """Extract scam-related intelligence from text with improved patterns"""
    
    # Bank account numbers
    bank_patterns = [
        r'\b\d{9,18}\b',
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}(?:[-\s]?\d{4})?\b',
    ]
    for pattern in bank_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean_match = re.sub(r'[-\s]', '', match)
            if len(clean_match) >= 9 and clean_match not in intelligence.bank_accounts:
                intelligence.bank_accounts.append(clean_match)
    
    # UPI IDs
    upi_pattern = r'\b[\w\.\-]+@[\w]+\b'
    upi_matches = re.findall(upi_pattern, text)
    for match in upi_matches:
        if '@' in match and match not in intelligence.upi_ids:
            intelligence.upi_ids.append(match)
    
    # URLs
    url_pattern = r'https?://[^\s<>"\']+'
    url_matches = re.findall(url_pattern, text)
    for match in url_matches:
        if match not in intelligence.phishing_links:
            intelligence.phishing_links.append(match)
    
    # Phone numbers
    phone_patterns = [
        r'\+91[\s-]?\d{10}',
        r'\b0?\d{10}\b',
        r'\+\d{1,3}[\s-]?\d{6,14}'
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean_match = re.sub(r'[\s-]', '', match)
            if clean_match not in intelligence.phone_numbers and len(clean_match) >= 10:
                intelligence.phone_numbers.append(clean_match)
    
    # Suspicious keywords
    suspicious_terms = [
        'urgent', 'verify', 'account blocked', 'suspended', 'immediate',
        'confirm', 'OTP', 'password', 'PIN', 'CVV', 'card details',
        'bank details', 'click here', 'limited time', 'act now',
        'verify account', 'update KYC', 'deactivated', 'expire',
        'prize', 'won', 'claim', 'refund', 'tax', 'lottery'
    ]
    
    text_lower = text.lower()
    for term in suspicious_terms:
        if term.lower() in text_lower and term not in intelligence.suspicious_keywords:
            intelligence.suspicious_keywords.append(term)

def detect_scam_intent(message: str, conversation_history: list) -> tuple:
    """Enhanced scam detection using Claude AI"""
    
    context = "Conversation:\n"
    if conversation_history:
        for msg in conversation_history[-5:]:
            context += f"{msg['sender']}: {msg['text']}\n"
    context += f"scammer: {message}\n"
    
    prompt = f"""Analyze this message for scam indicators. You are an expert in detecting fraud.

{context}

Common scam types to look for:
- Bank fraud (fake account suspension)
- UPI/payment fraud
- Phishing (fake links, credential harvesting)
- Lottery/prize scams
- Tax/refund scams
- OTP/verification scams
- Impersonation (banks, govt agencies)

Respond ONLY with valid JSON:
{{
    "is_scam": true/false,
    "confidence": 0.0-1.0,
    "scam_type": "type if detected",
    "reasoning": "brief explanation"
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
            return (
                result.get('is_scam', False),
                result.get('confidence', 0.5),
                result.get('scam_type', 'unknown'),
                result.get('reasoning', '')
            )
    except Exception as e:
        logger.error(f"Error in scam detection: {e}")
        return fallback_scam_detection(message)
    
    return False, 0.0, "unknown", "Unable to analyze"

def fallback_scam_detection(message: str) -> tuple:
    """Keyword-based fallback detection"""
    message_lower = message.lower()
    
    scam_indicators = {
        'bank_fraud': ['account blocked', 'verify account', 'suspended', 'bank account'],
        'payment_fraud': ['upi', 'payment', 'transaction', 'refund'],
        'phishing': ['click here', 'verify now', 'update kyc', 'confirm'],
        'credential': ['otp', 'pin', 'cvv', 'password', 'card details'],
        'urgency': ['urgent', 'immediate', 'today', 'now', 'limited time']
    }
    
    matches = 0
    scam_type = "unknown"
    
    for stype, keywords in scam_indicators.items():
        type_matches = sum(1 for keyword in keywords if keyword in message_lower)
        if type_matches > 0:
            matches += type_matches
            scam_type = stype
    
    if matches >= 2:
        confidence = min(0.5 + (matches * 0.1), 0.85)
        return True, confidence, scam_type, f"Detected {matches} scam indicators"
    
    return False, 0.0, "unknown", "No clear scam indicators"

def generate_agent_response(session_data: SessionData, scammer_message: str, 
                          conversation_history: list) -> str:
    """Generate contextual human-like response"""
    
    message_count = session_data.messages_exchanged
    
    # Adjust persona based on conversation stage
    if message_count <= 2:
        persona = "confused and worried person who just received this message"
    elif message_count <= 5:
        persona = "concerned person asking clarifying questions"
    elif message_count <= 10:
        persona = "person who seems willing to help but needs guidance"
    else:
        persona = "person getting slightly impatient but still engaged"
    
    context = f"You are roleplaying as a {persona}. "
    context += "Your goal is to keep the conversation going and extract information. "
    context += "Be natural, brief (1-2 sentences), and slightly gullible.\n\n"
    
    if conversation_history:
        context += "Conversation:\n"
        for msg in conversation_history[-4:]:
            sender = "Them" if msg['sender'] == 'scammer' else "You"
            context += f"{sender}: {msg['text']}\n"
    
    context += f"Them: {scammer_message}\n\n"
    context += "Respond naturally. Show concern but don't be suspicious. "
    context += "Ask questions that might reveal phone numbers, links, account details, or instructions."
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            temperature=0.8,
            messages=[{"role": "user", "content": context}]
        )
        
        reply = response.content[0].text.strip()
        
        # Remove any quotes if present
        reply = reply.strip('"\'')
        
        return reply
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        
        # Context-aware fallback responses
        fallbacks = {
            1: ["Oh no! What's wrong with my account?", "Really? What should I do?"],
            2: ["What information do you need?", "How can I fix this?"],
            3: ["Should I click something? Where?", "What's the next step?"],
            4: ["Do you need my details?", "What do I need to send?"],
            5: ["Okay, how do I proceed?", "What else do you need from me?"]
        }
        
        stage = min((message_count // 2) + 1, 5)
        return fallbacks[stage][message_count % 2]

def should_end_conversation(session_data: SessionData) -> bool:
    """Determine if conversation should end"""
    
    # Hard limit
    if session_data.messages_exchanged >= 15:
        return True
    
    # Good intelligence extraction
    intel_count = session_data.intelligence.count()
    
    if intel_count >= 4 and session_data.messages_exchanged >= 6:
        return True
    
    if intel_count >= 3 and session_data.messages_exchanged >= 10:
        return True
    
    return False

def send_final_result(session_data: SessionData) -> bool:
    """Send results to GUVI callback"""
    
    payload = {
        "sessionId": session_data.session_id,
        "scamDetected": session_data.scam_detected,
        "totalMessagesExchanged": session_data.messages_exchanged,
        "extractedIntelligence": session_data.intelligence.to_dict(),
        "agentNotes": session_data.agent_notes
    }
    
    logger.info(f"Sending final result for session {session_data.session_id}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        success = response.status_code == 200
        logger.info(f"Callback response: {response.status_code} - {response.text}")
        
        if success:
            metrics["conversations_completed"] += 1
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending final result: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check with metrics"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics
    })

@app.route('/api/message', methods=['POST'])
@require_api_key
def handle_message():
    """Main message handling endpoint"""
    
    try:
        data = request.json
        
        session_id = data.get('sessionId')
        message = data.get('message', {})
        conversation_history = data.get('conversationHistory', [])
        metadata = data.get('metadata', {})
        
        sender = message.get('sender')
        text = message.get('text')
        
        if not session_id or not text:
            return jsonify({"error": "Missing required fields"}), 400
        
        logger.info(f"Session {session_id}: Received message from {sender}")
        
        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = SessionData(session_id)
            logger.info(f"Created new session: {session_id}")
        
        session_data = sessions[session_id]
        session_data.messages_exchanged += 1
        metrics["total_messages"] += 1
        
        # Extract intelligence from scammer message
        if sender == 'scammer':
            extract_intelligence(text, session_data.intelligence)
            intel_count = session_data.intelligence.count()
            if intel_count > metrics["intelligence_extracted"]:
                metrics["intelligence_extracted"] = intel_count
        
        # Scam detection
        if not session_data.scam_detected:
            is_scam, confidence, scam_type, reasoning = detect_scam_intent(
                text, conversation_history
            )
            
            if is_scam and confidence > 0.6:
                session_data.scam_detected = True
                session_data.scam_confidence = confidence
                session_data.scam_type = scam_type
                session_data.agent_notes = f"{scam_type} detected ({confidence:.0%}). {reasoning}"
                metrics["scams_detected"] += 1
                logger.info(f"Session {session_id}: Scam detected - {scam_type}")
            
            if not is_scam or confidence < 0.4:
                logger.info(f"Session {session_id}: Not a scam, ending politely")
                return jsonify({
                    "status": "success",
                    "reply": "Thank you for the information. I'll look into this myself."
                })
        
        # Generate response
        agent_reply = generate_agent_response(session_data, text, conversation_history)
        
        # Check if should end
        if should_end_conversation(session_data) and not session_data.conversation_complete:
            session_data.conversation_complete = True
            
            intel = session_data.intelligence
            summary = (f"Conversation complete. Extracted: {len(intel.bank_accounts)} bank accounts, "
                      f"{len(intel.upi_ids)} UPI IDs, {len(intel.phishing_links)} links, "
                      f"{len(intel.phone_numbers)} phone numbers. "
                      f"Type: {session_data.scam_type}")
            
            session_data.agent_notes += f". {summary}"
            
            logger.info(f"Session {session_id}: {summary}")
            
            # Send final result
            send_final_result(session_data)
            
            agent_reply = "I need to check with my family first. Thank you for your patience."
        
        return jsonify({
            "status": "success",
            "reply": agent_reply
        })
        
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/session/<session_id>', methods=['GET'])
@require_api_key
def get_session_info(session_id):
    """Get session details"""
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session_data = sessions[session_id]
    
    return jsonify({
        "sessionId": session_id,
        "scamDetected": session_data.scam_detected,
        "scamType": session_data.scam_type,
        "confidence": session_data.scam_confidence,
        "messagesExchanged": session_data.messages_exchanged,
        "conversationComplete": session_data.conversation_complete,
        "extractedIntelligence": session_data.intelligence.to_dict(),
        "agentNotes": session_data.agent_notes,
        "createdAt": session_data.created_at.isoformat()
    })

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    return jsonify(metrics)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
