# Windows Setup Guide

Complete setup instructions for running the Honeypot API on Windows.

## 📋 Prerequisites

- Windows 10 or 11
- Python 3.11 or 3.12 (NOT 3.14)
- Internet connection

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Python 3.12

1. Download: https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
2. Run installer
3. ✅ Check "Add Python to PATH"
4. ✅ Check "Install for all users"
5. Click "Install Now"

### Step 2: Extract the Project

1. Extract `honeypot-scam-detection.zip` to a folder
2. Example: `C:\Users\vivek\Music\honeypot-scam-detection\`

### Step 3: Open PowerShell/Command Prompt

```powershell
# Navigate to project folder
cd C:\Users\vivek\Music\honeypot-scam-detection

# Or wherever you extracted the files
```

### Step 4: Create Virtual Environment

```powershell
# Create virtual environment with Python 3.12
py -3.12 -m venv .venv

# Activate it
.venv\Scripts\activate

# You should see (.venv) in your prompt
```

### Step 5: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install packages
pip install -r requirements.txt

# Install waitress (Windows-compatible server)
pip install waitress
```

### Step 6: Configure API Keys

```powershell
# Copy example env file
copy .env.example .env

# Edit .env file with Notepad
notepad .env
```

**In .env file, set:**
```dotenv
HONEYPOT_API_KEY=ljscbbdbcjdsjsnks
ANTHROPIC_API_KEY=sk-ant-your-new-key-here
PORT=5000
```

**Important:**
- No quotes around values
- Get Anthropic API key from: https://console.anthropic.com
- Save and close

### Step 7: Add Root Route (Important!)

Open `app.py` and add this route after the health check:

```python
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
        }
    })
```

### Step 8: Run the Server

```powershell
# Simple way (development)
python app.py

# OR production-like way
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### Step 9: Test It!

**Open browser and go to:**
```
http://localhost:5000/
```

You should see the API welcome message!

**Test health check:**
```
http://localhost:5000/health
```

**Run automated tests:**
```powershell
# In a NEW PowerShell window
cd C:\Users\vivek\Music\honeypot-scam-detection
.venv\Scripts\activate
python test_api.py
```

## ✅ Verification Checklist

- [ ] Python 3.12 installed (`python --version`)
- [ ] Virtual environment created (`.venv` folder exists)
- [ ] Virtual environment activated (see `(.venv)` in prompt)
- [ ] Dependencies installed (`pip list`)
- [ ] `.env` file created with API keys
- [ ] Root route added to `app.py`
- [ ] Server starts without errors
- [ ] Browser shows welcome page at `http://localhost:5000/`
- [ ] Tests pass (`python test_api.py`)

## 🐛 Common Issues on Windows

### Issue 1: "py: command not found"

**Solution:** Use `python` instead:
```powershell
python -m venv .venv
```

### Issue 2: "gunicorn doesn't work"

**Solution:** Don't use gunicorn on Windows! Use:
```powershell
python app.py
# OR
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### Issue 3: "No module named 'fcntl'"

**Cause:** Trying to use gunicorn (Linux-only)

**Solution:** Use waitress or Flask's built-in server (see above)

### Issue 4: "Python 3.14 compatibility error"

**Solution:** Install Python 3.12:
- Download from python.org
- Recreate venv with `py -3.12 -m venv .venv`

### Issue 5: "Permission denied" when creating venv

**Solution:** Run PowerShell as Administrator or use:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 6: "Port 5000 already in use"

**Solution:** Change port in .env:
```dotenv
PORT=5001
```

Or find and kill the process:
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

## 📁 Project Structure

```
honeypot-scam-detection/
├── .env                    # Your config (create from .env.example)
├── .env.example           # Example configuration
├── .venv/                 # Virtual environment (created by you)
├── app.py                 # Main application ⭐
├── app_advanced.py        # Advanced version with logging
├── requirements.txt       # Python dependencies
├── test_api.py           # Test suite
├── README.md             # Full documentation
├── QUICKSTART.md         # Quick start guide
├── DEPLOYMENT.md         # Cloud deployment guide
├── TROUBLESHOOTING.md    # Common problems & solutions
├── WINDOWS_SETUP.md      # This file
├── Dockerfile            # For Docker deployment
├── docker-compose.yml    # Docker Compose config
└── setup.sh             # Linux/Mac setup script
```

## 🎯 Different Ways to Run

### 1. Development (Recommended for testing)

```powershell
python app.py
```

**Pros:** 
- Simple
- Auto-reload on code changes
- Easy debugging

**Cons:**
- Single-threaded
- Not for production

### 2. Production-like (Waitress)

```powershell
waitress-serve --host=0.0.0.0 --port=5000 --threads=4 app:app
```

**Pros:**
- Multi-threaded
- Better performance
- Production-ready

**Cons:**
- No auto-reload

### 3. With Custom Script

Create `run.py`:

```python
from waitress import serve
from app import app

if __name__ == '__main__':
    print("🚀 Starting Honeypot API...")
    serve(app, host='0.0.0.0', port=5000, threads=4)
```

Run:
```powershell
python run.py
```

## 🧪 Testing the API

### Browser Tests (GET requests)

```
http://localhost:5000/          - Welcome page
http://localhost:5000/health    - Health check
```

### PowerShell Test (POST request)

```powershell
$headers = @{
    "x-api-key" = "ljscbbdbcjdsjsnks"
    "Content-Type" = "application/json"
}

$body = @{
    sessionId = "test-001"
    message = @{
        sender = "scammer"
        text = "Your bank account will be blocked!"
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    }
    conversationHistory = @()
    metadata = @{
        channel = "SMS"
        language = "English"
        locale = "IN"
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:5000/api/message" -Method Post -Headers $headers -Body $body
```

### Python Test Script

```powershell
python test_api.py
```

## 📊 Expected Output

When server starts:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

When you visit `/health`:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T12:00:00.000000"
}
```

## 🔒 Security Reminders

- ✅ Never commit `.env` to Git
- ✅ Use strong HONEYPOT_API_KEY
- ✅ Keep ANTHROPIC_API_KEY secret
- ✅ Don't share API keys publicly
- ✅ Rotate keys periodically

## 🚀 Next Steps

1. Test locally with `python test_api.py`
2. Verify scam detection works
3. Check intelligence extraction
4. Deploy to cloud (see DEPLOYMENT.md)
5. Submit to GUVI hackathon

## 💡 Pro Tips

1. **Use multiple terminals:**
   - Terminal 1: Run server
   - Terminal 2: Run tests
   - Terminal 3: Check logs

2. **View detailed logs:**
   Add to app.py:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Auto-reload during development:**
   ```powershell
   set FLASK_ENV=development
   python app.py
   ```

4. **Monitor API usage:**
   Check console.anthropic.com regularly

## 📞 Getting Help

If stuck:
1. Check TROUBLESHOOTING.md
2. Review error messages carefully
3. Verify all checklist items
4. Test each component separately

## 🎉 You're Ready!

Once the server runs and tests pass, you're all set to detect scams! 🎣

For deployment to cloud platforms, see **DEPLOYMENT.md**.

Good luck with the hackathon! 🏆
