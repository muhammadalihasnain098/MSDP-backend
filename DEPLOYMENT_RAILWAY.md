# Railway Deployment Guide - MSDP Backend

Complete guide to deploy Django backend with Celery on Railway (30-day free trial, NO CARD required to start).

---

## 🎯 Why Railway?

- ✅ **NO credit card** required to start trial
- ✅ **$5 credit + 30 days** trial period
- ✅ **Full Celery + Redis** support (real-time ML training)
- ✅ **PostgreSQL** included
- ✅ **Auto-deploy** from GitHub
- ✅ **After trial**: $1/month free tier OR upgrade to $5/month

---

## 📋 Prerequisites

- GitHub account with MSDP-backend repository ✅ (already done)
- Active GitHub profile (for verification)
- Vercel account (where frontend is deployed)

---

## 🚀 Step 1: Sign Up for Railway

### 1.1 Create Account (NO CARD REQUIRED)

1. Go to **https://railway.app**
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway to access your GitHub
4. **No credit card asked** - you get $5 credit immediately

### 1.2 Verify Trial Status

After signup, check your trial type:

- **Full Trial** ✅: Can deploy apps + databases (GitHub verified)
- **Limited Trial** ⚠️: Only databases (need to upgrade for apps)

If you get "Limited Trial", you can:
- Try verification at https://railway.app/verify
- OR upgrade to Hobby plan ($5/month - card required then)

**Most GitHub accounts get Full Trial automatically!**

---

## 🚀 Step 2: Deploy Django Backend

### 2.1 Create New Project

1. In Railway dashboard, click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. Select **"ali08642/MSDP-backend"**
4. Railway will:
   - Detect Python automatically
   - Find `Procfile` (web command)
   - Start building

### 2.2 Let Initial Build Complete

Wait for first build (~3-5 minutes). It will **fail** - that's expected! We need to add database and environment variables first.

---

## 🚀 Step 3: Add PostgreSQL Database

### 3.1 Add Database Service

1. In your project, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway automatically:
   - Creates PostgreSQL database
   - Sets `DATABASE_URL` environment variable
   - Links it to your web service

### 3.2 Verify Database Connection

1. Click on the **PostgreSQL** service
2. Go to **"Variables"** tab
3. You'll see `DATABASE_URL` - Railway provides this automatically

---

## 🚀 Step 4: Add Redis for Celery

### 4.1 Add Redis Service

1. Click **"New"** → **"Database"** → **"Add Redis"**
2. Railway automatically:
   - Creates Redis instance
   - Sets `REDIS_URL` environment variable
   - Links it to your services

---

## 🚀 Step 5: Configure Environment Variables

### 5.1 Go to Web Service Settings

1. Click on your **Django web service** (MSDP-backend)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**

### 5.2 Add Required Variables

Add these one by one (Railway auto-provides DATABASE_URL and REDIS_URL):

**SECRET_KEY** (generate new one):
```bash
# Run this locally to generate:
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Copy the output and add as `SECRET_KEY`

**Other Variables:**
```
DEBUG=False
FRONTEND_URL=https://your-vercel-app.vercel.app
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
CELERY_TASK_ALWAYS_EAGER=False
```

**Note:** Railway uses `${{VARIABLE}}` syntax to reference other variables.

### 5.3 Set ALLOWED_HOSTS (After Deployment)

You'll add this after getting your Railway URL in the next step.

---

## 🚀 Step 6: Get Your Railway URL and Update Settings

### 6.1 Generate Domain

1. Go to your **web service** → **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. You'll get a URL like: `msdp-backend-production-xxxx.up.railway.app`

### 6.2 Add ALLOWED_HOSTS

1. Go back to **"Variables"** tab
2. Add new variable:
   ```
   ALLOWED_HOSTS=msdp-backend-production-xxxx.up.railway.app
   ```
   (Replace with your actual Railway domain)

### 6.3 Trigger Redeploy

1. Go to **"Deployments"** tab
2. Click the **"⋮"** menu on latest deployment
3. Click **"Redeploy"**

---

## 🚀 Step 7: Run Database Migrations

### 7.1 Access Railway Shell

1. In your web service, go to **"Deployments"** tab
2. Click on the **active deployment** (green checkmark)
3. Scroll down, you'll see **"Service Logs"**
4. Look for **"Deploy Logs"** section

### 7.2 Run Migrations via Local Railway CLI

**Install Railway CLI:**
```powershell
# Install via npm
npm install -g @railway/cli

# OR download from https://railway.app/cli
```

**Login and Link:**
```powershell
# Login to Railway
railway login

# Navigate to your backend folder
cd D:\Github\MSDP-backend

# Link to your project
railway link
```
(Select your project from the list)

**Run Migrations:**
```powershell
# Run migrations in Railway environment
railway run python manage.py migrate

# Collect static files
railway run python manage.py collectstatic --noinput

# Create superuser
railway run python manage.py createsuperuser
```

### 7.3 Alternative: Add to Procfile (Automated)

If you want migrations to run automatically on each deploy, update `Procfile`:

```bash
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn config.wsgi --bind 0.0.0.0:$PORT
```

**Commit and push:**
```powershell
git add Procfile
git commit -m "Add automatic migrations on deploy"
git push
```

Railway will auto-redeploy and run migrations.

---

## 🚀 Step 8: Add Celery Worker Service

### 8.1 Create Worker Service

1. In your project, click **"New"** → **"Empty Service"**
2. Click **"Connect to GitHub"**
3. Select **"ali08642/MSDP-backend"** (same repo)
4. Railway detects Python but **won't use Procfile's web command**

### 8.2 Override Start Command

1. Go to worker service → **"Settings"** tab
2. Scroll to **"Deploy"** section
3. Click **"Start Command"** → Enable override
4. Enter:
   ```
   celery -A config worker --loglevel=info --pool=solo
   ```
5. Click **"Deploy"**

### 8.3 Add Environment Variables to Worker

Worker needs same variables as web service:

1. Go to worker service → **"Variables"** tab
2. Click **"+ New Variable"** → **"Add Reference"**
3. Select **"All variables from MSDP-backend service"**
4. This copies all env vars automatically

**Or manually add:**
```
SECRET_KEY=same-as-web-service
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
CELERY_TASK_ALWAYS_EAGER=False
```

### 8.4 Verify Worker Running

1. Check worker **"Deployments"** tab
2. Look for logs showing:
   ```
   [INFO] celery@worker ready
   [INFO] worker: Warm shutdown
   ```

---

## 🚀 Step 9: Update Vercel Frontend

### 9.1 Set Backend URL

1. Go to **Vercel dashboard**
2. Select your **MSDP** project
3. **Settings** → **Environment Variables**
4. Update/Add:
   ```
   NEXT_PUBLIC_API_URL=https://msdp-backend-production-xxxx.up.railway.app
   ```
   (Use your Railway domain from Step 6)

### 9.2 Redeploy Frontend

1. Go to **"Deployments"** tab in Vercel
2. Click **"⋮"** on latest deployment → **"Redeploy"**
3. Wait for deployment to complete

### 9.3 Update Django CORS Settings

Your `config/settings.py` should already have:
```python
CORS_ALLOWED_ORIGINS = [
    os.getenv('FRONTEND_URL', 'http://localhost:3000'),
]
```

This automatically allows your Vercel frontend! ✅

---

## 🚀 Step 10: Test Everything

### 10.1 Verify API Endpoints

Visit these URLs (replace with your Railway domain):

1. **Admin Panel:**
   ```
   https://msdp-backend-production-xxxx.up.railway.app/admin
   ```
   Login with superuser credentials

2. **API Health Check:**
   ```
   https://msdp-backend-production-xxxx.up.railway.app/api/forecasting/data-range/?disease=MALARIA
   ```
   Should return JSON with date ranges

3. **Available Forecasts:**
   ```
   https://msdp-backend-production-xxxx.up.railway.app/api/forecasting/forecasts/available_dates/?disease=MALARIA
   ```

### 10.2 Test ML Training

1. Go to your frontend: `https://your-app.vercel.app/admin/dashboard`
2. Navigate to **Model Training** tab
3. Configure training session:
   - Select disease (Malaria/Dengue)
   - Choose training date range
   - Choose forecast date range
4. Click **"Start Training"**
5. Watch status change: PENDING → TRAINING → COMPLETED

**Check Celery logs:**
- Go to Railway worker service → **"Deployments"** → **Logs**
- You should see training progress

### 10.3 Test Forecasts

1. Go to **Health Official Dashboard**
2. View forecasts with custom date queries
3. Export data if needed

---

## 📊 Monitor Your Usage

### Check Credit Balance

1. Railway dashboard → Click your profile (top right)
2. Select **"Usage"**
3. You'll see:
   - Credit remaining (out of $5)
   - Days remaining (out of 30)
   - Current usage rate

### Optimize Usage

**To make $5 last 30 days:**

1. **Scale down when not using:**
   - Pause services when not demoing
   - Settings → **"Sleep mode"** (manual pause)

2. **Monitor logs:**
   - Check for infinite loops or errors
   - Reduce unnecessary database queries

3. **Reduce replicas:**
   - Settings → **"Replicas"** → Set to 1 (default)

**Typical usage for your app:**
- Web service: ~$0.008/hour
- Celery worker: ~$0.008/hour
- PostgreSQL: ~$0.001/hour
- Redis: ~$0.001/hour

**Total: ~$0.018/hour = ~$13/month**

To stay under $5 for 30 days:
- Run only during demos (~8 hours/day = $4.32/month) ✅
- OR optimize and reduce resources

---

## 🐛 Troubleshooting

### Build Failed

**Check logs:**
1. Go to **"Deployments"** → Click failed deployment
2. Read **"Build Logs"**

**Common issues:**
- Missing dependencies: Check `requirements.txt`
- Python version: Verify `runtime.txt` has `python-3.12.0`

### Database Connection Error

**Error:** `could not connect to database`

**Fix:**
1. Verify PostgreSQL service is running (green checkmark)
2. Check `DATABASE_URL` exists in Variables
3. Ensure web service is linked to database

### Celery Not Processing Tasks

**Error:** Tasks stuck at PENDING

**Check:**
1. Worker service is running (green checkmark)
2. Worker has `REDIS_URL` variable
3. Check worker logs for errors

**Debug command:**
```powershell
railway run -s worker celery -A config inspect active
```

### CORS Errors

**Error:** `Access-Control-Allow-Origin`

**Fix:**
1. Verify `FRONTEND_URL` in Railway Variables matches Vercel URL exactly
2. Check `CORS_ALLOWED_ORIGINS` in `settings.py`
3. Redeploy after changes

### 502 Bad Gateway

**Error:** Gateway timeout

**Causes:**
- App hasn't started yet (wait 1-2 minutes)
- Migrations failed (check logs)
- Environment variables missing

**Fix:**
```powershell
# Check if app is running
railway logs

# Restart service
railway run python manage.py check
```

---

## 💰 After Trial Ends (30 Days or $5 Used)

### Option 1: Upgrade to Hobby Plan

**Cost:** $5/month minimum
- Includes $5 usage credit
- If usage < $5, you pay only $5
- If usage > $5, you pay extra

**To upgrade:**
1. Railway dashboard → **"Upgrade"**
2. Add credit card
3. Select **Hobby Plan**

### Option 2: Migrate to PythonAnywhere (Free Forever)

**If you can't/don't want to pay:**

1. Follow `DEPLOYMENT_FREE_NO_CARD.md` guide
2. Export data from Railway PostgreSQL:
   ```powershell
   railway run pg_dump $DATABASE_URL > backup.sql
   ```
3. Deploy on PythonAnywhere with MySQL
4. Import lab test and pharmacy data via Django admin
5. Update Vercel with PythonAnywhere URL

**Trade-offs:**
- ✅ Free forever
- ❌ Scheduled tasks instead of real-time Celery
- ❌ Limited CPU (100 sec/day)

### Option 3: Keep Free Tier ($1/month)

After trial, Railway gives $1/month credit:
- Enough for small databases
- NOT enough for web apps (need Hobby plan)

---

## 📈 Production Checklist

Before going live:

- [ ] `DEBUG=False` in environment variables
- [ ] `SECRET_KEY` is strong and unique (50+ chars)
- [ ] `ALLOWED_HOSTS` set correctly
- [ ] Database migrations completed
- [ ] Superuser created
- [ ] Static files collected
- [ ] CORS configured for Vercel
- [ ] Initial data uploaded (lab tests, pharmacy sales)
- [ ] Test all API endpoints
- [ ] Test ML training flow
- [ ] Test forecast generation
- [ ] Monitor logs for errors
- [ ] Set up Railway alerts (Usage > $4)

---

## 🎯 Quick Commands Reference

```powershell
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
cd D:\Github\MSDP-backend
railway link

# Run commands in Railway environment
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py collectstatic --noinput

# View logs
railway logs

# Check Celery
railway run -s worker celery -A config inspect active

# Database backup
railway run pg_dump $DATABASE_URL > backup.sql

# Open Railway dashboard
railway open
```

---

## 📞 Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app

---

## ✅ Summary

**What you deployed:**
- ✅ Django REST API (web service)
- ✅ Celery Worker (background tasks)
- ✅ PostgreSQL Database
- ✅ Redis (Celery broker)

**Your URLs:**
- Backend: `https://msdp-backend-production-xxxx.up.railway.app`
- Admin: `https://msdp-backend-production-xxxx.up.railway.app/admin`
- Frontend: `https://your-app.vercel.app`

**Trial limits:**
- $5 credit OR 30 days (whichever first)
- After trial: Upgrade ($5/month) or migrate (free PythonAnywhere)

**You're live!** 🚀

Test your ML forecasting system end-to-end with real-time training powered by Celery!
