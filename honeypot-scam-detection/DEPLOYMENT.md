# Deployment Guide - Agentic Honeypot API

This guide covers deploying the honeypot API to various cloud platforms.

## Table of Contents
1. [Local Deployment](#local-deployment)
2. [Railway Deployment](#railway-deployment)
3. [Render Deployment](#render-deployment)
4. [Heroku Deployment](#heroku-deployment)
5. [AWS Deployment](#aws-deployment)
6. [Google Cloud Run](#google-cloud-run)

---

## Local Deployment

### Prerequisites
- Python 3.8+
- Anthropic API key

### Steps

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your keys

# 3. Run locally
python app.py
```

**Test the API:**
```bash
curl http://localhost:5000/health
```

---

## Railway Deployment

Railway is recommended for quick deployment with automatic HTTPS.

### Steps

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login to Railway:**
```bash
railway login
```

3. **Initialize project:**
```bash
railway init
```

4. **Set environment variables:**
```bash
railway variables set ANTHROPIC_API_KEY=your-anthropic-key
railway variables set HONEYPOT_API_KEY=your-secret-key
```

5. **Deploy:**
```bash
railway up
```

6. **Get your URL:**
```bash
railway domain
```

Your API will be available at: `https://your-project.up.railway.app`

---

## Render Deployment

### Via Dashboard

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** honeypot-api
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

5. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `HONEYPOT_API_KEY`

6. Click "Create Web Service"

### Via render.yaml

Create `render.yaml`:

```yaml
services:
  - type: web
    name: honeypot-api
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: HONEYPOT_API_KEY
        sync: false
```

Then deploy:
```bash
render deploy
```

---

## Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed

### Steps

1. **Login to Heroku:**
```bash
heroku login
```

2. **Create app:**
```bash
heroku create honeypot-scam-detector
```

3. **Set environment variables:**
```bash
heroku config:set ANTHROPIC_API_KEY=your-key
heroku config:set HONEYPOT_API_KEY=your-secret-key
```

4. **Create Procfile:**
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 app:app
```

5. **Deploy:**
```bash
git push heroku main
```

6. **Open app:**
```bash
heroku open
```

---

## AWS Deployment

### Using AWS Elastic Beanstalk

1. **Install EB CLI:**
```bash
pip install awsebcli
```

2. **Initialize:**
```bash
eb init -p python-3.11 honeypot-api
```

3. **Create environment:**
```bash
eb create honeypot-prod
```

4. **Set environment variables:**
```bash
eb setenv ANTHROPIC_API_KEY=your-key HONEYPOT_API_KEY=your-secret-key
```

5. **Deploy:**
```bash
eb deploy
```

### Using AWS Lambda + API Gateway

Create `lambda_handler.py`:

```python
from app import app
import serverless_wsgi

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
```

Deploy with Serverless Framework or AWS SAM.

---

## Google Cloud Run

### Steps

1. **Create Dockerfile** (already provided)

2. **Build and push to Google Container Registry:**
```bash
gcloud builds submit --tag gcr.io/[PROJECT-ID]/honeypot-api
```

3. **Deploy to Cloud Run:**
```bash
gcloud run deploy honeypot-api \
  --image gcr.io/[PROJECT-ID]/honeypot-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=your-key,HONEYPOT_API_KEY=your-secret-key
```

---

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t honeypot-api .

# Run container
docker run -p 5000:5000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e HONEYPOT_API_KEY=your-secret-key \
  honeypot-api
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Production Checklist

Before deploying to production:

- [ ] Set strong `HONEYPOT_API_KEY`
- [ ] Configure proper logging
- [ ] Set up monitoring (e.g., Sentry, DataDog)
- [ ] Enable rate limiting
- [ ] Configure CORS if needed
- [ ] Set up database for session storage (Redis recommended)
- [ ] Enable HTTPS (automatic on most platforms)
- [ ] Configure health checks
- [ ] Set up alerts for errors
- [ ] Review security headers
- [ ] Test callback to GUVI endpoint
- [ ] Load test the API

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key for Claude |
| `HONEYPOT_API_KEY` | Yes | Secret key for API authentication |
| `PORT` | No | Port to run on (default: 5000) |

---

## Testing Deployment

After deployment, test with:

```bash
# Health check
curl https://your-api-url.com/health

# Test message (replace API key and URL)
curl -X POST https://your-api-url.com/api/message \
  -H "x-api-key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "Your account is suspended. Verify now!",
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

---

## Troubleshooting

### Issue: Timeout errors
**Solution:** Increase timeout in gunicorn command:
```bash
gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 app:app
```

### Issue: Memory errors
**Solution:** Reduce worker count or upgrade instance:
```bash
gunicorn -w 2 -b 0.0.0.0:$PORT app:app
```

### Issue: API key not working
**Solution:** Check environment variables are set:
```bash
# Railway
railway variables

# Heroku
heroku config

# Render
Check dashboard → Environment
```

### Issue: GUVI callback fails
**Solution:** Check network connectivity and logs. Ensure your deployment can make outbound HTTPS requests.

---

## Performance Optimization

1. **Use Redis for sessions:**
   - Add Redis to your deployment
   - Update session storage in code

2. **Enable caching:**
   - Cache scam detection patterns
   - Cache common responses

3. **Horizontal scaling:**
   - Increase worker count
   - Deploy multiple instances
   - Use load balancer

4. **Monitor performance:**
   - Track response times
   - Monitor Claude API usage
   - Set up alerts

---

## Support

For deployment issues:
1. Check platform-specific logs
2. Verify environment variables
3. Test locally first
4. Review error messages

---

**Happy Deploying! 🚀**
