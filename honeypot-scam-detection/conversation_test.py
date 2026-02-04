import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
API_KEY = "ljscbbdbcjdsjsnks"

print("💬 Multi-Turn Scam Conversation Test")
print("=" * 60)

session_id = "conversation-test-001"
conversation_history = []

def send_message(sender, text):
    """Send a message and get response"""
    
    message_data = {
        "sender": sender,
        "text": text,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/message",
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "sessionId": session_id,
            "message": message_data,
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
    )
    
    reply = response.json().get('reply', '')
    
    # Add to history
    conversation_history.append(message_data)
    if reply:
        conversation_history.append({
            "sender": "user",
            "text": reply,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    return reply

# Message 1
print("\n[Scammer]: Your bank account will be blocked today! Verify now!")
reply1 = send_message("scammer", "Your bank account will be blocked today! Verify now!")
print(f"[AI Bot]: {reply1}")

# Message 2
print("\n[Scammer]: Send money to verify123@paytm immediately!")
reply2 = send_message("scammer", "Send money to verify123@paytm immediately!")
print(f"[AI Bot]: {reply2}")

# Message 3
print("\n[Scammer]: Your account number 9876543210987 needs verification. Click: http://fake-bank.com")
reply3 = send_message("scammer", "Your account number 9876543210987 needs verification. Click: http://fake-bank.com")
print(f"[AI Bot]: {reply3}")

# Check intelligence
print("\n" + "=" * 60)
print("📊 Final Intelligence Report:")
print("=" * 60)

session_response = requests.get(
    f"{BASE_URL}/api/session/{session_id}",
    headers={"x-api-key": API_KEY}
)

data = session_response.json()
intel = data['extractedIntelligence']

print(f"\n✅ Scam Detected: {data['scamDetected']}")
print(f"✅ Confidence: {data['confidence']:.0%}")
print(f"✅ Messages Exchanged: {data['messagesExchanged']}")

print(f"\n🎯 Extracted Intelligence:")
print(f"  - UPI IDs: {intel['upiIds']}")
print(f"  - Bank Accounts: {intel['bankAccounts']}")
print(f"  - Phishing Links: {intel['phishingLinks']}")
print(f"  - Phone Numbers: {intel['phoneNumbers']}")
print(f"  - Suspicious Keywords: {intel['suspiciousKeywords'][:5]}")

print(f"\n📝 Agent Notes: {data['agentNotes']}")
print("\n" + "=" * 60)
print("✅ Conversation Test Complete!")