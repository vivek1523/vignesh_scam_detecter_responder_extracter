from flask import Flask, request, jsonify
import anthropic
import os
import re
import requests
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json
from dotenv import load_dotenv
import httpx
import warnings

# Import database module
from database import (
    init_database, save_session, save_message, 
    update_guvi_callback_status, get_session as db_get_session,
    get_all_sessions, get_statistics, get_conversation_history
)

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

# Initialize database
print("Initializing database...")
init_database()

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

# Session storage (in-memory cache + database)
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
        self.scam_type = ""
        self.created_at = datetime.now(timezone.utc)

def extract_intelligence(text: str, intelligence: ScamIntelligence):
    """Extract scam-related intelligence from text"""
    
    # Extract bank account numbers
    bank_patterns = [
        r'\b\d{9,18}\b',
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    ]
    for pattern in bank_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean = re.sub(r'[-\s]', '', match)
            if len(clean) >= 9 and clean not in intelligence.bank_accounts:
                intelligence.bank_accounts.append(clean)
    
    # Extract UPI IDs
    upi_pattern = r'\b[\w\.\-]+@[\w]+\b'
    upi_matches = re.findall(upi_pattern, text)
    for match in upi_matches:
        if '@' in match and match not in intelligence.upi_ids:
            intelligence.upi_ids.append(match)
    
    # Extract URLs
    url_pattern = r'https?://[^\s<>"\']+'
    url_matches = re.findall(url_pattern, text)
    for match in url_matches:
        if match not in intelligence.phishing_links:
            intelligence.phishing_links.append(match)
    
    # Extract phone numbers
    phone_patterns = [
        r'\+91[\s-]?\d{10}',
        r'\b0?\d{10}\b',
        r'\+\d{1,3}[\s-]?\d{6,14}'
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean = re.sub(r'[\s-]', '', match)
            if clean not in intelligence.phone_numbers and len(clean) >= 10:
                intelligence.phone_numbers.append(clean)
    
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
            return (
                result.get('is_scam', False),
                result.get('confidence', 0.5),
                result.get('scam_type', 'unknown'),
                result.get('reasoning', '')
            )
        
    except Exception as e:
        print(f"Error in scam detection: {e}")
        return fallback_scam_detection(message)
    
    return False, 0.0, "unknown", "Unable to analyze"

def fallback_scam_detection(message: str) -> tuple:
    """Simple keyword-based scam detection as fallback"""
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

def generate_agent_response(session_data: SessionData, scammer_message: str, conversation_history: List[Dict]) -> str:
    """Generate a human-like response using Claude AI Agent"""
    
    message_count = session_data.messages_exchanged
    
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
        
        reply = response.content[0].text.strip().strip('"\'')
        return reply
        
    except Exception as e:
        print(f"Error generating response: {e}")
        
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
    
    if session_data.messages_exchanged >= 15:
        return True
    
    intel_count = session_data.intelligence.count()
    
    if intel_count >= 4 and session_data.messages_exchanged >= 6:
        return True
    
    if intel_count >= 3 and session_data.messages_exchanged >= 10:
        return True
    
    return False

def send_final_result(session_data: SessionData) -> bool:
    """Send final results to GUVI callback endpoint"""
    
    payload = {
        "sessionId": session_data.session_id,
        "scamDetected": session_data.scam_detected,
        "totalMessagesExchanged": session_data.messages_exchanged,
        "extractedIntelligence": session_data.intelligence.to_dict(),
        "agentNotes": session_data.agent_notes
    }
    
    print(f"Sending final result for session {session_data.session_id}")
    
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        success = response.status_code == 200
        print(f"Callback response: {response.status_code}")
        
        # Update database with callback status
        update_guvi_callback_status(session_data.session_id, response.status_code)
        
        return success
        
    except Exception as e:
        print(f"Error sending final result: {e}")
        update_guvi_callback_status(session_data.session_id, -1)
        return False

@app.route('/', methods=['GET'])
def index():
    """Welcome page"""
    return jsonify({
        "message": "🎣 Honeypot Scam Detection API",
        "status": "running",
        "version": "2.0",
        "database": "SQLite enabled",
        "endpoints": {
            "health": "/health",
            "message": "/api/message (POST)",
            "session": "/api/session/<session_id> (GET)",
            "sessions": "/api/sessions (GET)",
            "statistics": "/api/statistics (GET)",
            "export": "/api/export (GET)"
        },
        "documentation": "See README.md for usage instructions"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = get_statistics()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "total_sessions": stats.get('total_sessions', 0),
        "scams_detected": stats.get('scams_detected', 0)
    })

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
        timestamp = message.get('timestamp')
        
        if not session_id or not text:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = SessionData(session_id)
        
        session_data = sessions[session_id]
        session_data.messages_exchanged += 1
        
        # Save message to database
        save_message(session_id, sender, text, timestamp)
        
        # Extract intelligence from scammer message
        if sender == 'scammer':
            extract_intelligence(text, session_data.intelligence)
        
        # Detect scam intent
        if not session_data.scam_detected:
            is_scam, confidence, scam_type, reasoning = detect_scam_intent(text, conversation_history)
            
            if is_scam and confidence > 0.6:
                session_data.scam_detected = True
                session_data.scam_confidence = confidence
                session_data.scam_type = scam_type
                session_data.agent_notes = f"{scam_type} detected ({confidence:.0%}). {reasoning}"
            
            if not is_scam or confidence < 0.4:
                # Save session even if not a scam
                save_session(session_data)
                return jsonify({
                    "status": "success",
                    "reply": "Thank you for the information. I'll look into this."
                })
        
        # Generate agent response
        agent_reply = generate_agent_response(session_data, text, conversation_history)
        
        # Save agent reply to database
        save_message(session_id, 'user', agent_reply, datetime.now(timezone.utc).isoformat())
        
        # Check if should end conversation
        if should_end_conversation(session_data) and not session_data.conversation_complete:
            session_data.conversation_complete = True
            
            intel = session_data.intelligence
            summary = (f"Conversation complete. Extracted: {len(intel.bank_accounts)} bank accounts, "
                      f"{len(intel.upi_ids)} UPI IDs, {len(intel.phishing_links)} links, "
                      f"{len(intel.phone_numbers)} phone numbers. Type: {session_data.scam_type}")
            
            session_data.agent_notes += f". {summary}"
            
            print(f"Session {session_id}: {summary}")
            
            # Save final session to database
            save_session(session_data)
            
            # Send final result to GUVI
            send_final_result(session_data)
            
            agent_reply = "I need to check with my family first. I'll get back to you."
        else:
            # Save intermediate session state
            save_session(session_data)
        
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
    """Get session details from memory or database"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Try memory first
    if session_id in sessions:
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
            "source": "memory"
        })
    
    # Try database
    db_session = db_get_session(session_id)
    if db_session:
        return jsonify({
            "sessionId": db_session['session_id'],
            "scamDetected": bool(db_session['scam_detected']),
            "scamType": db_session['scam_type'],
            "confidence": db_session['scam_confidence'],
            "messagesExchanged": db_session['messages_exchanged'],
            "conversationComplete": db_session['completed_at'] is not None,
            "extractedIntelligence": {
                "bankAccounts": json.loads(db_session['bank_accounts']),
                "upiIds": json.loads(db_session['upi_ids']),
                "phishingLinks": json.loads(db_session['phishing_links']),
                "phoneNumbers": json.loads(db_session['phone_numbers']),
                "suspiciousKeywords": json.loads(db_session['suspicious_keywords'])
            },
            "agentNotes": db_session['agent_notes'],
            "createdAt": db_session['created_at'],
            "completedAt": db_session['completed_at'],
            "guviCallbackSent": bool(db_session['guvi_callback_sent']),
            "source": "database"
        })
    
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions from database"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    limit = request.args.get('limit', 100, type=int)
    sessions_list = get_all_sessions(limit)
    
    return jsonify({
        "total": len(sessions_list),
        "sessions": sessions_list
    })

@app.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """Get full conversation history for a session"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    messages = get_conversation_history(session_id)
    
    return jsonify({
        "sessionId": session_id,
        "messageCount": len(messages),
        "messages": messages
    })

@app.route('/api/statistics', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    stats = get_statistics()
    
    return jsonify(stats)

@app.route('/api/export', methods=['GET'])
def export_data():
    """Export data to CSV"""
    
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    from database import export_to_csv
    
    filename = f"scam_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    success = export_to_csv(filename)
    
    if success:
        return jsonify({
            "status": "success",
            "filename": filename,
            "message": f"Data exported to {filename}"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Export failed"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"🎣 Honeypot Scam Detection API v2.0")
    print(f"{'='*60}")
    print(f"Database: SQLite (scam_intelligence.db)")
    print(f"Port: {port}")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
