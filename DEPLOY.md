# Catalog AI Suite - Deployment Guide

This guide provides step-by-step instructions for deploying the Catalog AI Suite MVP on Render (backend) and Vercel (frontend).

## Overview

- **Backend**: FastAPI + Celery worker + Redis (on Render)
- **Frontend**: React 19 + Vite (on Vercel)
- **Database**: PostgreSQL (Render Postgres or Supabase)
- **Authentication**: Google OAuth 2.0

---

## Prerequisites

1. GitHub account with the repository pushed
2. Render account (free tier works)
3. Vercel account (free tier works)
4. Google Cloud Console project with OAuth credentials
5. Hugging Face account (for model access)

---

## Step 1: Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: **Web application**
6. Add authorized redirect URIs:
   - `http://localhost:8000/auth/google/callback` (local dev)
   - `https://your-render-app.onrender.com/auth/google/callback` (production)
7. Note down:
   - **Google Client ID**
   - **Google Client Secret**

---

## Step 2: Set Up Database

### Option A: Render Postgres (Recommended)

1. In Render dashboard, click "New" → "PostgreSQL"
2. Choose free tier
3. Note the **Internal Database URL** (looks like `postgresql://user:pass@host:5432/dbname`)
4. Keep this URL secure - you'll need it for environment variables

### Option B: Supabase PostgreSQL

1. Go to [Supabase](https://supabase.com/)
2. Create a new project
3. Go to Settings → Database
4. Copy the **Connection String** (URI mode)
5. Use this as your `DATABASE_URL`

---

## Step 3: Set Up Redis

### Option A: Upstash Redis (Recommended for Render Free Tier)

1. Go to [Upstash](https://upstash.com/)
2. Create a new Redis database
3. Copy the **REST URL** and **REST Token**
4. These will be used as `UPSTASH_REDIS_REST_URL` and `UPSTRESH_REDIS_REST_TOKEN`

### Option B: Render Redis

1. In Render dashboard, click "New" → "Redis"
2. Choose free tier
3. Copy the connection URL

---

## Step 4: Deploy Backend to Render

### 4.1 Create Web Service

1. In Render dashboard, click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `catalog-ai-api`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 2 --timeout 120`
   - **Plan**: Free (or Starter for better performance)

### 4.2 Add Environment Variables

In the Render web service settings, add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | From Step 2 | PostgreSQL connection string |
| `REDIS_URL` | From Step 3 | Redis connection string |
| `GOOGLE_CLIENT_ID` | From Step 1 | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | From Step 1 | Google OAuth client secret |
| `JWT_SECRET` | Generate random | Use `openssl rand -hex 32` |
| `HF_TOKEN` | Your HF token | Hugging Face API token |
| `UPLOAD_DIR` | `/tmp/uploads` | Writable directory on Render |
| `TRAINING_DATA_DIR` | `/tmp/training_data` | Writable directory |
| `ANOMALY_THRESHOLD` | `0.7` | Anomaly detection threshold |
| `CORS_ORIGINS` | `https://your-vercel-app.vercel.app` | Frontend URL |

### 4.3 Create Worker Service

1. In Render dashboard, click "New" → "Background Worker"
2. Connect the same GitHub repository
3. Configure:
   - **Name**: `catalog-ai-worker`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && celery -A app.celery worker --loglevel=info --pool=solo`
4. Add the same environment variables as the web service

### 4.4 Update render.yaml (Optional)

If using Infrastructure as Code, update the `render.yaml` file:

```yaml
services:
  - type: web
    name: catalog-ai-api
    env: python
    region: oregon
    plan: free
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 2 --timeout 120"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - fromGroup: catalog-ai-env

  - type: worker
    name: catalog-ai-worker
    env: python
    region: oregon
    plan: free
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && celery -A app.celery worker --loglevel=info --pool=solo"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - fromGroup: catalog-ai-env

envVarGroups:
  - name: catalog-ai-env
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
      - key: GOOGLE_CLIENT_ID
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false
      - key: JWT_SECRET
        generateValue: true
      - key: HF_TOKEN
        sync: false
```

---

## Step 5: Deploy Frontend to Vercel

### 5.1 Prepare Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

### 5.2 Create Vercel Project

1. Go to [Vercel](https://vercel.com/)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### 5.3 Add Environment Variables

In Vercel project settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_API_URL` | `https://catalog-ai-api.onrender.com` | Your Render backend URL |
| `VITE_GOOGLE_CLIENT_ID` | From Step 1 | Same Google Client ID |

### 5.4 Deploy

1. Click "Deploy"
2. Wait for build to complete
3. Note your production URL (e.g., `https://your-app.vercel.app`)

---

## Step 6: Seed Demo Data

After deployment, seed the database with demo data:

### Option A: Via SSH (Render)

```bash
# Connect to Render instance
render ssh catalog-ai-api

# Run seed script
cd backend
python -m app.seed --email demo@example.com
```

### Option B: Via API Endpoint

Create an admin endpoint to trigger seeding (add to main.py):

```python
@app.post("/admin/seed")
async def seed_demo_data(current_user: User = Depends(get_current_admin_user)):
    from .seed import seed_database
    seed_database()
    return {"message": "Database seeded successfully"}
```

Then call: `POST https://your-render-app.onrender.com/admin/seed`

---

## Step 7: Test the Deployment

1. Open your Vercel frontend URL in a browser
2. Sign in with Google (use the demo email if seeded)
3. Upload a product image
4. Verify real-time status updates
5. Check extracted attributes and anomaly warnings
6. Edit attributes and download CSV

---

## Local Development Setup

### Prerequisites

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install Node.js dependencies
cd ../frontend
npm install
```

### Environment Variables (.env)

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/catalog_ai
REDIS_URL=redis://localhost:6379/0
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret
JWT_SECRET=local_dev_secret_key
HF_TOKEN=your_huggingface_token
UPLOAD_DIR=./backend/uploads
TRAINING_DATA_DIR=./backend/app/ml/training_data
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

### Run with Docker Compose

```bash
docker-compose up -d
```

Services available:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Run Locally Without Docker

```bash
# Start PostgreSQL and Redis
# macOS: brew services start postgresql && brew services start redis
# Or use Docker just for these: docker-compose up -d db redis

# Seed database
cd backend
python -m app.seed --email demo@example.com

# Start backend
uvicorn app.main:app --reload --port 8000

# In another terminal, start frontend
cd frontend
npm run dev
```

---

## Troubleshooting

### Backend Issues

**Models not loading:**
- Ensure `HF_TOKEN` is set correctly
- Check Render logs for download errors
- First deployment may take 5-10 minutes for model download

**Database connection errors:**
- Verify `DATABASE_URL` is correct
- Ensure database allows connections from Render IPs
- Check SSL mode in connection string

**CORS errors:**
- Add your Vercel URL to `CORS_ORIGINS`
- Ensure middleware is configured in `main.py`

### Frontend Issues

**Login not working:**
- Verify Google Client ID matches between backend and frontend
- Check browser console for errors
- Ensure redirect URIs are configured in Google Console

**API calls failing:**
- Check `VITE_API_URL` points to correct backend
- Verify backend is running and accessible
- Check network tab for 401/403 errors

---

## Security Considerations

1. **Never commit `.env` files** to version control
2. **Rotate secrets regularly** (JWT_SECRET, database passwords)
3. **Use HTTPS only** in production (automatic on Render/Vercel)
4. **Enable rate limiting** on auth endpoints (not implemented yet)
5. **Validate file uploads** for size and type (partially implemented)
6. **Encrypt sensitive data** (Shopify tokens) before storing

---

## Monitoring & Logs

### Render Logs

- View logs in Render dashboard
- Set up alerts for errors
- Monitor memory usage (free tier has limits)

### Vercel Analytics

- Enable Vercel Analytics for frontend
- Monitor Core Web Vitals
- Track user flows

---

## Scaling Considerations

When ready to scale:

1. **Upgrade Render plan** for more resources
2. **Add CDN** for image delivery (Cloudflare, CloudFront)
3. **Implement caching** (Redis already configured)
4. **Add monitoring** (Sentry, Datadog)
5. **Set up CI/CD** pipelines
6. **Implement proper queue system** (Celery with Redis/RabbitMQ)

---

## Support

For issues or questions:
- Check existing issues on GitHub
- Review Render/Vercel documentation
- Contact support team

---

**Last Updated**: May 2024
**Version**: 1.0.0
