import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
API_KEY = "ljscbbdbcjdsjsnks"  # Your HONEYPOT_API_KEY

print("🎣 Manual Scam Detection Test")
print("=" * 60)

# Test 1: Send a scam message
print("\n📨 Sending scam message...")

response = requests.post(
    f"{BASE_URL}/api/message",
    headers={
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "sessionId": "manual-test-001",
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your bank account will be blocked today. Verify immediately by sending money to scammer@paytm",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
)

print(f"Status: {response.status_code}")
print(f"AI Response: {json.dumps(response.json(), indent=2)}")

# Test 2: Check what was extracted
print("\n🔍 Checking extracted intelligence...")

session_response = requests.get(
    f"{BASE_URL}/api/session/manual-test-001",
    headers={"x-api-key": API_KEY}
)

print(f"Status: {session_response.status_code}")
print(f"Session Data: {json.dumps(session_response.json(), indent=2)}")

print("\n" + "=" * 60)
print("✅ Test Complete!")