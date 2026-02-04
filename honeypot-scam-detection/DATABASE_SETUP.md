# 🚀 Database Version - Quick Setup Guide

Complete guide to run the honeypot with SQLite database storage.

## 📋 What You Need

1. Python 3.12 installed ✅
2. Your `.env` file configured ✅
3. Virtual environment activated ✅

## 🎯 3-Minute Setup

### **Step 1: Make Sure You're in the Right Folder**

```bash
cd C:\Users\vivek\Music\honeypot-scam-detection
```

### **Step 2: Activate Virtual Environment**

```bash
.venv\Scripts\activate
```

You should see `(.venv)` in your prompt.

### **Step 3: Run the Database Version**

```bash
python app_with_database.py
```

**Expected output:**
```
Initializing database...
✓ Database initialized successfully
Initializing Anthropic client...
✓ Anthropic client initialized successfully
============================================================
🎣 Honeypot Scam Detection API v2.0
============================================================
Database: SQLite (scam_intelligence.db)
Port: 5000
============================================================
 * Running on http://127.0.0.1:5000
```

### **Step 4: Test It**

Open a **NEW** terminal:

```bash
cd C:\Users\vivek\Music\honeypot-scam-detection
.venv\Scripts\activate
python test_with_db.py
```

### **Step 5: View Dashboard (Optional)**

Open **ANOTHER** terminal:

```bash
cd C:\Users\vivek\Music\honeypot-scam-detection
.venv\Scripts\activate
python dashboard.py
```

Then open browser: **http://localhost:8080**

---

## 🎉 You're Done!

You now have:
- ✅ API running with database storage
- ✅ All scam data saved permanently
- ✅ Web dashboard to view data
- ✅ Full conversation history

---

## 📊 What's Different from v1.0?

| Feature | Old (app.py) | New (app_with_database.py) |
|---------|-------------|----------------------------|
| Data Storage | Memory only | SQLite database |
| Restart | ❌ Data lost | ✅ Data persists |
| View History | ❌ No | ✅ Yes |
| Dashboard | ❌ No | ✅ Yes |
| Export | ❌ No | ✅ CSV export |
| Analysis | ❌ No | ✅ SQL queries |

---

## 🔍 Checking Your Data

### **Method 1: Dashboard** (Easiest)

```bash
python dashboard.py
# Open http://localhost:8080
```

### **Method 2: API Query**

```bash
curl -H "x-api-key: ljscsnsssskssssfdrfgvdc" \
  http://localhost:5000/api/statistics
```

### **Method 3: Database File**

```bash
# Check if database exists
dir scam_intelligence.db

# Query it
sqlite3 scam_intelligence.db "SELECT COUNT(*) FROM scam_sessions;"
```

### **Method 4: Python Script**

```python
from database import get_statistics

stats = get_statistics()
print(f"Total scams detected: {stats['scams_detected']}")
```

---

## 💾 Your Database File

**Location:** `scam_intelligence.db` (in project folder)

**What's inside:**
- All scam sessions
- Every conversation message
- Extracted intelligence
- Statistics and metadata

**Backup it:**
```bash
copy scam_intelligence.db backup\scam_intelligence_backup.db
```

---

## 🎯 Common Tasks

### **View All Sessions**

```bash
curl -H "x-api-key: ljscsnsssskssssfdrfgvdc" \
  http://localhost:5000/api/sessions?limit=10
```

### **View Specific Conversation**

```bash
curl -H "x-api-key: ljscsnsssskssssfdrfgvdc" \
  http://localhost:5000/api/conversation/session-123
```

### **Export to CSV**

```bash
curl -H "x-api-key: ljscsnsssskssssfdrfgvdc" \
  http://localhost:5000/api/export
```

### **Get Statistics**

```bash
curl -H "x-api-key: ljscsnsssskssssfdrfgvdc" \
  http://localhost:5000/api/statistics
```

---

## 🐛 Troubleshooting

### **"Database is locked" error**

Close the dashboard and any database browser tools, then restart.

### **"No such table" error**

The database wasn't initialized. Run:
```bash
python -c "from database import init_database; init_database()"
```

### **Dashboard shows no data**

Make sure you've run some tests first:
```bash
python test_with_db.py
```

### **Can't find database file**

It's created automatically in the project folder when you first run the API.

---

## 📁 File Overview

| File | Purpose | When to Use |
|------|---------|-------------|
| `app_with_database.py` | Main API with DB | Always use this |
| `database.py` | Database module | Auto-imported |
| `dashboard.py` | Web viewer | To view data |
| `test_with_db.py` | Tests | To verify it works |
| `scam_intelligence.db` | SQLite DB | Auto-created |

---

## 🎓 Next Steps

1. **Test It**: Run `python test_with_db.py`
2. **View Dashboard**: Run `python dashboard.py`
3. **Send Real Scams**: Use the API to detect scams
4. **Analyze Data**: Query the database
5. **Export**: Save data to CSV
6. **Deploy**: Same as v1.0, just use `app_with_database.py`

---

## 💡 Pro Tips

1. **Keep Dashboard Open** - Monitor scams in real-time
2. **Backup Regularly** - Copy `scam_intelligence.db`
3. **Export to CSV** - For Excel analysis
4. **Use SQL Queries** - For advanced analysis
5. **Monitor Database Size** - Clean old data if needed

---

## ✅ Checklist

Before deployment:

- [ ] `app_with_database.py` runs without errors
- [ ] `test_with_db.py` passes all tests
- [ ] Dashboard shows data at http://localhost:8080
- [ ] Database file exists (`scam_intelligence.db`)
- [ ] `.env` file has correct API keys
- [ ] Backup strategy in place

---

## 🚀 Deploy to Production

Same as before! Just use `app_with_database.py` instead of `app.py`.

**Don't forget to:**
- Include `database.py` file
- Set file permissions for `.db` file
- Backup database regularly
- Monitor database growth

---

**🎉 Enjoy your permanent scam intelligence storage!** 💾
