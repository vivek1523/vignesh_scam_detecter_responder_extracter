import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = os.getenv("HONEYPOT_API_KEY")

if not API_KEY:
    print("ERROR: HONEYPOT_API_KEY not found in .env file!")
    exit(1)

print(f"Using API Key: {API_KEY[:15]}...")

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "=" * 60)
    print("TEST 1: HEALTH CHECK")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Health check passed!")
        print(f"   Database: {data.get('database')}")
        print(f"   Total Sessions: {data.get('total_sessions', 0)}")
        print(f"   Scams Detected: {data.get('scams_detected', 0)}")
        return True
    else:
        print("❌ Health check failed!")
        return False

def test_scam_conversation():
    """Test full scam conversation with database storage"""
    print("\n" + "=" * 60)
    print("TEST 2: SCAM CONVERSATION WITH DATABASE")
    print("=" * 60)
    
    session_id = f"test-db-session-{int(time.time())}"
    conversation_history = []
    
    # Message 1: Initial threat
    print("\n[Message 1] Scammer threatens account closure...")
    msg1 = {
        "sender": "scammer",
        "text": "URGENT! Your bank account will be blocked today. Verify immediately!",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response1 = requests.post(
        f"{BASE_URL}/api/message",
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "sessionId": session_id,
            "message": msg1,
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
    )
    
    print(f"Status: {response1.status_code}")
    if response1.status_code == 200:
        reply1 = response1.json().get('reply', '')
        print(f"AI Reply: {reply1}")
        
        conversation_history.append(msg1)
        conversation_history.append({
            "sender": "user",
            "text": reply1,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Message 2: Request UPI and account
        time.sleep(1)
        print("\n[Message 2] Scammer requests payment details...")
        msg2 = {
            "sender": "scammer",
            "text": "Send money to fraudster@paytm and provide account number 9876543210987 to verify.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response2 = requests.post(
            f"{BASE_URL}/api/message",
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "sessionId": session_id,
                "message": msg2,
                "conversationHistory": conversation_history,
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
        )
        
        print(f"Status: {response2.status_code}")
        if response2.status_code == 200:
            reply2 = response2.json().get('reply', '')
            print(f"AI Reply: {reply2}")
            
            conversation_history.append(msg2)
            conversation_history.append({
                "sender": "user",
                "text": reply2,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Message 3: Phishing link
            time.sleep(1)
            print("\n[Message 3] Scammer sends phishing link...")
            msg3 = {
                "sender": "scammer",
                "text": "Click here to verify: https://fake-bank-verify.com/urgent and call +919876543210",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            response3 = requests.post(
                f"{BASE_URL}/api/message",
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "sessionId": session_id,
                    "message": msg3,
                    "conversationHistory": conversation_history,
                    "metadata": {
                        "channel": "SMS",
                        "language": "English",
                        "locale": "IN"
                    }
                }
            )
            
            print(f"Status: {response3.status_code}")
            if response3.status_code == 200:
                reply3 = response3.json().get('reply', '')
                print(f"AI Reply: {reply3}")
                
                # Check session data
                print("\n[Checking database storage...]")
                time.sleep(2)  # Give database time to save
                
                session_response = requests.get(
                    f"{BASE_URL}/api/session/{session_id}",
                    headers={"x-api-key": API_KEY}
                )
                
                print(f"Status: {session_response.status_code}")
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    
                    print(f"\n📊 Session Data (Source: {session_data.get('source')})")
                    print(f"   Scam Detected: {session_data.get('scamDetected')}")
                    print(f"   Scam Type: {session_data.get('scamType')}")
                    print(f"   Confidence: {session_data.get('confidence', 0):.0%}")
                    print(f"   Messages: {session_data.get('messagesExchanged')}")
                    
                    intel = session_data.get('extractedIntelligence', {})
                    print(f"\n🎯 Extracted Intelligence:")
                    print(f"   UPI IDs: {intel.get('upiIds', [])}")
                    print(f"   Bank Accounts: {intel.get('bankAccounts', [])}")
                    print(f"   Phishing Links: {intel.get('phishingLinks', [])}")
                    print(f"   Phone Numbers: {intel.get('phoneNumbers', [])}")
                    print(f"   Keywords: {intel.get('suspiciousKeywords', [])[:5]}")
                    
                    # Check conversation history
                    print("\n[Checking conversation history in database...]")
                    conv_response = requests.get(
                        f"{BASE_URL}/api/conversation/{session_id}",
                        headers={"x-api-key": API_KEY}
                    )
                    
                    if conv_response.status_code == 200:
                        conv_data = conv_response.json()
                        print(f"\n💬 Conversation History ({conv_data.get('messageCount')} messages)")
                        
                        for i, msg in enumerate(conv_data.get('messages', [])[:6], 1):
                            sender_icon = "🚨" if msg['sender'] == 'scammer' else "🤖"
                            print(f"   {i}. {sender_icon} {msg['sender']}: {msg['text'][:50]}...")
                        
                        print("\n✅ Database storage test passed!")
                        return True
                    else:
                        print(f"❌ Failed to get conversation history")
                        return False
                else:
                    print(f"❌ Failed to get session data")
                    return False
            else:
                print(f"❌ Message 3 failed")
                return False
        else:
            print(f"❌ Message 2 failed")
            return False
    else:
        print(f"❌ Message 1 failed")
        return False

def test_statistics():
    """Test statistics endpoint"""
    print("\n" + "=" * 60)
    print("TEST 3: STATISTICS")
    print("=" * 60)
    
    response = requests.get(
        f"{BASE_URL}/api/statistics",
        headers={"x-api-key": API_KEY}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        
        print(f"\n📈 Database Statistics:")
        print(f"   Total Sessions: {stats.get('total_sessions', 0)}")
        print(f"   Scams Detected: {stats.get('scams_detected', 0)}")
        print(f"   Detection Rate: {stats.get('detection_rate', 0):.1f}%")
        print(f"   Total Messages: {stats.get('total_messages', 0)}")
        print(f"   Intelligence Extracted: {stats.get('intelligence_extracted', 0)}")
        print(f"   Avg Confidence: {stats.get('average_confidence', 0):.0%}")
        
        print("\n✅ Statistics test passed!")
        return True
    else:
        print("❌ Statistics test failed!")
        return False

def test_sessions_list():
    """Test sessions list endpoint"""
    print("\n" + "=" * 60)
    print("TEST 4: SESSIONS LIST")
    print("=" * 60)
    
    response = requests.get(
        f"{BASE_URL}/api/sessions?limit=5",
        headers={"x-api-key": API_KEY}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n📋 Recent Sessions: {data.get('total', 0)} found")
        
        for i, session in enumerate(data.get('sessions', [])[:3], 1):
            print(f"\n   {i}. Session: {session.get('session_id', '')[:20]}...")
            print(f"      Scam: {bool(session.get('scam_detected'))}")
            print(f"      Type: {session.get('scam_type', 'N/A')}")
            print(f"      Messages: {session.get('messages_exchanged', 0)}")
            print(f"      Created: {session.get('created_at', 'N/A')}")
        
        print("\n✅ Sessions list test passed!")
        return True
    else:
        print("❌ Sessions list test failed!")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎣 HONEYPOT DATABASE TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health_check()))
    results.append(("Scam Conversation + DB", test_scam_conversation()))
    results.append(("Statistics", test_statistics()))
    results.append(("Sessions List", test_sessions_list()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("💾 Check scam_intelligence.db for saved data")
        print("🌐 Run dashboard.py to view in browser!")
    else:
        print("\n⚠️  Some tests failed. Check output above.")
    
    print()
