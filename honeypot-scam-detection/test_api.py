import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables to ensure we match main.py
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = os.getenv("HONEYPOT_API_KEY", "your-secret-api-key-here")

def get_timestamp():
    """Helper to get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def test_scam_conversation():
    """Test a complete scam conversation flow"""
    
    session_id = "test-session-12345"
    
    # ==========================================
    # TEST 1: Initial scam message
    # ==========================================
    print("=" * 60)
    print("TEST 1: Initial scam message")
    print("=" * 60)
    
    request1 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately.",
            "timestamp": get_timestamp()
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    response1 = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=request1
    )
    
    print(f"Request: {request1['message']['text']}")
    print(f"Status: {response1.status_code}")
    print(f"Response: {json.dumps(response1.json(), indent=2)}")
    
    if response1.status_code != 200:
        print("❌ Failed at first message. Check your API Key.")
        return
    
    reply1 = response1.json().get('reply')
    
    # ==========================================
    # TEST 2: Follow-up with UPI request
    # ==========================================
    print("\n" + "=" * 60)
    print("TEST 2: Follow-up with UPI request")
    print("=" * 60)
    
    request2 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Share your UPI ID scammer123@paytm and account number to avoid suspension.",
            "timestamp": get_timestamp()
        },
        "conversationHistory": [
            {"sender": "scammer", "text": request1['message']['text'], "timestamp": request1['message']['timestamp']},
            {"sender": "user", "text": reply1, "timestamp": get_timestamp()}
        ],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    response2 = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=request2
    )
    
    print(f"Request: {request2['message']['text']}")
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}")
    
    reply2 = response2.json().get('reply')
    
    # ==========================================
    # TEST 3: Phishing link
    # ==========================================
    print("\n" + "=" * 60)
    print("TEST 3: Phishing link")
    print("=" * 60)
    
    request3 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Click this link to verify: https://fake-bank-verify.com/urgent and enter your OTP",
            "timestamp": get_timestamp()
        },
        "conversationHistory": request2['conversationHistory'] + [
            {"sender": "scammer", "text": request2['message']['text'], "timestamp": request2['message']['timestamp']},
            {"sender": "user", "text": reply2, "timestamp": get_timestamp()}
        ],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    response3 = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=request3
    )
    
    print(f"Request: {request3['message']['text']}")
    print(f"Status: {response3.status_code}")
    print(f"Response: {json.dumps(response3.json(), indent=2)}")
    
    # ==========================================
    # SESSION INFORMATION
    # ==========================================
    print("\n" + "=" * 60)
    print("SESSION INFORMATION")
    print("=" * 60)
    
    session_response = requests.get(
        f"{BASE_URL}/api/session/{session_id}",
        headers={"x-api-key": API_KEY}
    )
    
    print(f"Status: {session_response.status_code}")
    print(f"Session Data: {json.dumps(session_response.json(), indent=2)}")

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "=" * 60)
    print("HEALTH CHECK")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_unauthorized_access():
    """Test that API requires authentication"""
    print("\n" + "=" * 60)
    print("UNAUTHORIZED ACCESS TEST")
    print("=" * 60)
    
    request_data = {
        "sessionId": "test",
        "message": {
            "sender": "scammer",
            "text": "Test",
            "timestamp": get_timestamp()
        },
        "conversationHistory": [],
        "metadata": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/message",
        headers={"x-api-key": "wrong-key", "Content-Type": "application/json"},
        json=request_data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("Expected: 401 Unauthorized ✓" if response.status_code == 401 else "FAILED")

if __name__ == "__main__":
    print("Starting Honeypot API Tests\n")
    
    # Run tests
    test_health_check()
    test_unauthorized_access()
    test_scam_conversation()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)