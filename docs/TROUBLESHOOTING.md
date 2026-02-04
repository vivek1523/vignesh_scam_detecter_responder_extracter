# Troubleshooting Guide

Common issues and their solutions when setting up the Honeypot API.

## Installation Issues

### Error: "TypeError: Client.__init__() got an unexpected keyword argument"

**Problem:** Incompatible Anthropic library version.

**Solution:**
```bash
# Uninstall old version
pip uninstall anthropic -y

# Install correct version
pip install anthropic==0.39.0

# Or reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Error: "ModuleNotFoundError: No module named 'anthropic'"

**Problem:** Dependencies not installed.

**Solution:**
```bash
pip install -r requirements.txt
```

### Error: "Permission denied" when installing packages

**Problem:** Missing write permissions.

**Solution:**
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Or install with --user flag
pip install -r requirements.txt --user
```

---

## Runtime Issues

### Error: "Unauthorized" (401)

**Problem:** API key mismatch.

**Solutions:**

1. **Check your .env file exists:**
```bash
ls -la .env
```

2. **Verify the API key in .env matches your request:**
```bash
# .env file should contain:
HONEYPOT_API_KEY=your-secret-api-key-here
```

3. **Make sure you're passing the correct header:**
```bash
curl -H "x-api-key: your-secret-api-key-here" http://localhost:5000/health
```

### Error: "Anthropic API error" or "Invalid API key"

**Problem:** Missing or invalid Anthropic API key.

**Solutions:**

1. **Get your API key:**
   - Go to https://console.anthropic.com
   - Sign up/login
   - Go to API Keys section
   - Create a new key

2. **Add to .env file:**
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

3. **Verify it's set:**
```bash
# On Linux/Mac
cat .env | grep ANTHROPIC

# Check in Python
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"
```

### Error: "Address already in use" or "Port 5000 is already allocated"

**Problem:** Port 5000 is occupied by another process.

**Solutions:**

1. **Use a different port:**
```bash
# In .env file
PORT=5001

# Or directly
PORT=5001 python app.py
```

2. **Find and kill the process using port 5000:**
```bash
# On Linux/Mac
lsof -ti:5000 | xargs kill -9

# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Error: "Connection refused" when testing

**Problem:** Server is not running.

**Solution:**
```bash
# Start the server first
python app.py

# Then in another terminal, run tests
python test_api.py
```

---

## API Issues

### Issue: No response from AI agent

**Problem:** Anthropic API call failing.

**Debug steps:**

1. **Check server logs for errors:**
```bash
# Look for error messages in terminal where app.py is running
```

2. **Test Anthropic API directly:**
```python
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("API works!", response.content[0].text)
except Exception as e:
    print(f"API error: {e}")
```

3. **Check API credits:**
   - Go to https://console.anthropic.com
   - Check your usage and billing

### Issue: Callback to GUVI endpoint fails

**Problem:** Network connectivity or incorrect payload.

**Debug steps:**

1. **Check the logs:**
```bash
# Look for "Error sending final result" in logs
```

2. **Test callback manually:**
```bash
curl -X POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-123",
    "scamDetected": true,
    "totalMessagesExchanged": 5,
    "extractedIntelligence": {
      "bankAccounts": [],
      "upiIds": [],
      "phishingLinks": [],
      "phoneNumbers": [],
      "suspiciousKeywords": ["urgent"]
    },
    "agentNotes": "Test callback"
  }'
```

3. **Check firewall/network settings:**
   - Ensure your deployment can make outbound HTTPS requests
   - Check if there's a firewall blocking the connection

### Issue: Intelligence not being extracted

**Problem:** Regex patterns not matching or scammer not providing data.

**Solutions:**

1. **Check session data:**
```bash
curl http://localhost:5000/api/session/your-session-id \
  -H "x-api-key: your-secret-api-key-here"
```

2. **Test extraction manually:**
```python
import re

text = "My UPI is scammer@paytm and account is 1234567890123"

# Bank accounts
bank_matches = re.findall(r'\b\d{9,18}\b', text)
print(f"Banks: {bank_matches}")

# UPI IDs
upi_matches = re.findall(r'\b[\w\.\-]+@[\w]+\b', text)
print(f"UPI: {upi_matches}")
```

3. **Review conversation history:**
   - Scammers need to actually provide the information
   - Agent needs 5-10 messages to extract good data

---

## Dependency Issues

### Error: "No matching distribution found for anthropic==0.39.0"

**Problem:** Package version not available or Python version too old.

**Solution:**
```bash
# Try latest stable version
pip install anthropic

# Or specific compatible version
pip install "anthropic>=0.35.0"
```

### Error: Import errors for Flask or other packages

**Problem:** Incomplete installation.

**Solution:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Or install individually
pip install flask==3.0.0
pip install anthropic
pip install requests
pip install python-dotenv
pip install gunicorn
```

---

## Environment Issues

### Issue: .env file not being read

**Problem:** File not in correct location or not loaded.

**Solutions:**

1. **Verify file location:**
```bash
# Should be in the same directory as app.py
ls -la .env
```

2. **Load manually in Python:**
```python
from dotenv import load_dotenv
load_dotenv()  # This should be at the top of app.py
```

3. **Use absolute path:**
```python
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
```

### Issue: Environment variables not set in production

**Problem:** .env file doesn't work in production deployments.

**Solution:**
Set environment variables directly in your platform:

**Railway:**
```bash
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set HONEYPOT_API_KEY=your-secret-key
```

**Heroku:**
```bash
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku config:set HONEYPOT_API_KEY=your-secret-key
```

**Render:**
- Go to Dashboard → Environment
- Add variables manually

---

## Testing Issues

### Error: "Connection refused" when running test_api.py

**Problem:** Server not running or wrong URL.

**Solution:**
```bash
# Terminal 1: Start server
python app.py

# Terminal 2: Run tests (after server starts)
python test_api.py
```

### Error: Tests fail with 401 Unauthorized

**Problem:** API key in test script doesn't match .env.

**Solution:**
Edit `test_api.py` and update:
```python
API_KEY = "your-secret-api-key-here"  # Match this with .env
```

---

## Performance Issues

### Issue: Slow response times (>5 seconds)

**Causes and solutions:**

1. **Anthropic API latency:**
   - Normal for first request (cold start)
   - Subsequent requests should be faster

2. **Too many workers:**
```bash
# Reduce worker count
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

3. **Network issues:**
   - Check internet connection
   - Try different Anthropic model endpoint

### Issue: Memory errors

**Problem:** Not enough RAM.

**Solution:**
```bash
# Reduce workers
gunicorn -w 1 -b 0.0.0.0:5000 app:app

# Or upgrade your deployment instance
```

---

## Docker Issues

### Error: Docker build fails

**Solution:**
```bash
# Clean build
docker build --no-cache -t honeypot-api .

# Check Dockerfile syntax
cat Dockerfile
```

### Error: Container exits immediately

**Solution:**
```bash
# Check logs
docker logs <container-id>

# Run interactively
docker run -it honeypot-api /bin/bash

# Check environment variables are passed
docker run -e ANTHROPIC_API_KEY=sk-ant-... -e HONEYPOT_API_KEY=secret -p 5000:5000 honeypot-api
```

---

## Still Having Issues?

### Debugging Checklist

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip list`)
- [ ] .env file exists and has correct keys
- [ ] ANTHROPIC_API_KEY is valid
- [ ] HONEYPOT_API_KEY matches in .env and requests
- [ ] Port 5000 is available
- [ ] Server is running before testing
- [ ] Firewall allows connections
- [ ] Internet connection works

### Get Detailed Logs

Run with debug mode:
```python
# Add to app.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or run with debug flag
app.run(debug=True)
```

### Test Individual Components

**Test 1: Python imports**
```bash
python3 -c "import flask; import anthropic; import requests; print('All imports OK')"
```

**Test 2: Environment variables**
```bash
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY')[:10])"
```

**Test 3: Flask server**
```bash
python3 -c "from flask import Flask; app = Flask(__name__); print('Flask OK')"
```

**Test 4: Anthropic API**
```bash
python3 -c "import anthropic; import os; from dotenv import load_dotenv; load_dotenv(); client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')); print('Anthropic OK')"
```

### Contact Support

If none of these solutions work:

1. Check the error message carefully
2. Search for the error online
3. Review the README.md and QUICKSTART.md
4. Check if it's a known issue with the Anthropic library

---

**Remember:** Most issues are related to:
1. Missing/incorrect API keys (70%)
2. Wrong Python/package versions (20%)
3. Port conflicts (5%)
4. Other (5%)

Always check these first! 🔍
