# 🚀 Quick Start Guide

Get your AI-powered honeypot running in 5 minutes!

## Prerequisites

1. **Python 3.8+** installed
2. **Anthropic API Key** - Get one at [console.anthropic.com](https://console.anthropic.com)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your keys:

```env
HONEYPOT_API_KEY=my-super-secret-key-12345
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
PORT=5000
```

### 3. Start the Server

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### 4. Test It!

Open a new terminal and run:

```bash
python test_api.py
```

Or test manually:

```bash
curl http://localhost:5000/health
```

## 🎯 Making Your First Request

```bash
curl -X POST http://localhost:5000/api/message \
  -H "x-api-key: my-super-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo-session-001",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Your bank account will be blocked. Click here to verify: http://fake-bank.com",
      "timestamp": "2026-01-21T10:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "reply": "Oh no! What's wrong with my account? Should I click that link?"
}
```

## 🔍 Understanding the Flow

1. **Scammer sends message** → API receives it
2. **Claude AI analyzes** → Detects scam intent
3. **Agent activates** → Generates human-like response
4. **Intelligence extracted** → Bank accounts, UPI IDs, links, etc.
5. **Conversation continues** → Agent keeps extracting info
6. **Final callback sent** → Results sent to GUVI endpoint

## 📊 Check Session Status

```bash
curl http://localhost:5000/api/session/demo-session-001 \
  -H "x-api-key: my-super-secret-key-12345"
```

**Response shows:**
- Scam detection status
- Confidence level
- Extracted intelligence
- Message count
- Agent notes

## 🏗️ Project Structure

```
honeypot-api/
├── app.py                 # Main application (use this)
├── app_advanced.py        # Advanced version with logging
├── test_api.py           # Automated tests
├── requirements.txt      # Python dependencies
├── README.md            # Full documentation
├── DEPLOYMENT.md        # Deploy to cloud platforms
├── Dockerfile           # For Docker deployment
├── docker-compose.yml   # Docker Compose config
└── .env                 # Your configuration (create this)
```

## 🎨 Features Demonstration

### Feature 1: Scam Detection
The system automatically detects:
- Bank fraud attempts
- UPI/payment scams
- Phishing links
- OTP/credential theft
- Urgency tactics

### Feature 2: Intelligent Extraction
Automatically captures:
- Bank account numbers
- UPI IDs (e.g., scammer@paytm)
- Phone numbers
- Phishing URLs
- Suspicious keywords

### Feature 3: Human-like Agent
The AI agent:
- Sounds natural and believable
- Asks clarifying questions
- Shows appropriate concern
- Gradually appears to comply
- Never reveals it's a bot

## 🐛 Common Issues

### "Unauthorized" Error
**Problem:** API key doesn't match
**Solution:** Check your `x-api-key` header matches the `.env` file

### "Anthropic API Error"
**Problem:** Invalid or missing API key
**Solution:** Verify your `ANTHROPIC_API_KEY` in `.env`

### Port Already in Use
**Problem:** Port 5000 is occupied
**Solution:** Change `PORT` in `.env` to 5001 or run:
```bash
PORT=5001 python app.py
```

## 📈 What Happens Next?

After 8-15 messages or sufficient intelligence extraction:

1. Agent gracefully ends conversation
2. Final intelligence summary created
3. Results sent to GUVI callback endpoint:
   ```
   POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
   ```

## 🚀 Deploy to Production

**Quick Deploy to Railway:**
```bash
npm install -g @railway/cli
railway login
railway init
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set HONEYPOT_API_KEY=your-key
railway up
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more platforms.

## 📚 Next Steps

1. ✅ Test with different scam scenarios
2. ✅ Review extracted intelligence
3. ✅ Deploy to cloud platform
4. ✅ Monitor performance
5. ✅ Submit to GUVI hackathon

## 💡 Tips for Best Results

1. **Let conversations run:** The agent needs 5-10 messages to extract good intelligence
2. **Check session data:** Use `/api/session/{id}` to see what's been extracted
3. **Monitor logs:** Watch for scam detection confidence levels
4. **Test edge cases:** Try non-scam messages to ensure proper filtering

## 🎯 Success Metrics

Your system is working well if you see:
- ✅ Scam detection accuracy > 80%
- ✅ 3-5 intelligence items per conversation
- ✅ Natural, human-like responses
- ✅ < 2 second response time
- ✅ Successful GUVI callbacks

## 🤝 Need Help?

1. Check [README.md](README.md) for detailed docs
2. Review [DEPLOYMENT.md](DEPLOYMENT.md) for cloud setup
3. Run `python test_api.py` to verify setup
4. Check server logs for error details

---

**You're all set! Start catching scammers! 🎣**
