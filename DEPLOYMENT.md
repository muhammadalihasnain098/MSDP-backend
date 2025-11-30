# Deployment Guide - MSDP Backend

This guide explains how to deploy the MSDP backend to production using modern cloud services.

## 🌐 Deployment Architecture

```
Frontend (Vercel/Netlify) → Backend (Render/Railway) → PostgreSQL (Neon)
                                ↓
                          Redis (Upstash/Redis Cloud)
                                ↓
                          Celery Workers (Same as Backend)
```

## 📋 Pre-Deployment Checklist

- [ ] Code is tested and working locally
- [ ] All migrations are created and tested
- [ ] Environment variables are documented
- [ ] Static files configuration is correct
- [ ] CORS settings allow frontend domain
- [ ] Database backups strategy in place

## 🚀 Option 1: Deploy to Render.com (Recommended)

### Step 1: Prepare Your Code

1. **Create `Procfile`** (already created below)
2. **Create `runtime.txt`** (already created below)
3. **Push to GitHub**

### Step 2: Set Up PostgreSQL (Neon.tech)

1. Go to [neon.tech](https://neon.tech)
2. Create new project
3. Copy connection string (format: `postgresql://user:pass@host/db`)
4. Save as `DATABASE_URL`

### Step 3: Set Up Redis (Upstash)

1. Go to [upstash.com](https://upstash.com)
2. Create Redis database
3. Copy connection URL (format: `redis://user:pass@host:port`)
4. Save as `REDIS_URL`

### Step 4: Deploy to Render

1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Environment**: Python 3

5. Add Environment Variables:
   ```
   SECRET_KEY=your-generated-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app.onrender.com
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   FRONTEND_URL=https://your-frontend.vercel.app
   ```

6. Deploy!

### Step 5: Deploy Celery Worker (Separate Service on Render)

1. Create new Background Worker on Render
2. Same repository
3. **Start Command**: `celery -A config worker -l info`
4. Same environment variables

### Step 6: Deploy Celery Beat (Separate Service)

1. Create another Background Worker
2. **Start Command**: `celery -A config beat -l info`
3. Same environment variables

## 🚀 Option 2: Deploy to Railway.app

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Initialize Project

```bash
railway init
railway link
```

### Step 3: Add PostgreSQL

```bash
railway add --plugin postgresql
```

### Step 4: Add Redis

```bash
railway add --plugin redis
```

### Step 5: Set Environment Variables

```bash
railway variables set SECRET_KEY="your-secret-key"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS="${{RAILWAY_PUBLIC_DOMAIN}}"
railway variables set FRONTEND_URL="https://your-frontend.vercel.app"
```

### Step 6: Deploy

```bash
railway up
```

## 🎨 Frontend Deployment (Vercel)

### Step 1: Update Frontend API URL

In your Next.js project, create `.env.production`:

```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

### Step 2: Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd d:/Github/MSDP
vercel
```

Or connect your GitHub repo on [vercel.com](https://vercel.com)

## ⚙️ Production Settings

### Security Settings (settings.py)

```python
# Production-only settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Generate SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📊 Monitoring & Logging

### Check Logs (Render)

```bash
# View logs in Render dashboard
# Or use Render CLI
render logs -a your-service-name
```

### Check Logs (Railway)

```bash
railway logs
```

### Monitor Celery Tasks

Add Flower (Celery monitoring):

```bash
# Add to requirements.txt
flower==2.0.1

# Deploy as separate service
# Start Command: celery -A config flower
```

## 🔄 CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/deploy/srv-xxxxx
```

## 🗄️ Database Management

### Backup Database (Neon)

Neon provides automatic backups. Access from dashboard.

### Manual Backup

```bash
# From local machine
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Run Migrations on Production

```bash
# Render: Auto-runs in build command
# Or manually via SSH/Shell access

railway run python manage.py migrate
```

## 📈 Scaling

### Scale Web Server (Render)

- Upgrade plan for more resources
- Add horizontal scaling (multiple instances)

### Scale Celery Workers

- Add more worker instances
- Configure autoscaling based on queue size

### Database Scaling (Neon)

- Neon autoscales compute
- Upgrade for more storage/connections

## 🔐 Security Best Practices

1. **Never commit `.env` file**
2. **Use environment variables for secrets**
3. **Enable HTTPS only** (set SECURE_SSL_REDIRECT)
4. **Use strong SECRET_KEY**
5. **Keep dependencies updated**: `pip list --outdated`
6. **Enable database connection pooling**
7. **Rate limit API endpoints** (add django-ratelimit)

## 🐛 Troubleshooting

### Static files not loading

```bash
# Make sure this ran during deployment
python manage.py collectstatic --noinput
```

### Database migrations failing

```bash
# Check DATABASE_URL is correct
# Run migrations manually
railway run python manage.py migrate
```

### Celery not processing tasks

```bash
# Check Redis connection
# Ensure worker service is running
# Check logs for errors
```

### CORS errors from frontend

Check `CORS_ALLOWED_ORIGINS` includes your frontend URL.

## 📞 Support

For deployment issues:
- **Render**: [render.com/docs](https://render.com/docs)
- **Railway**: [docs.railway.app](https://docs.railway.app)
- **Neon**: [neon.tech/docs](https://neon.tech/docs)

## 🎯 Post-Deployment Tasks

- [ ] Test all API endpoints
- [ ] Verify Celery tasks execute
- [ ] Check scheduled tasks (Beat)
- [ ] Monitor error logs
- [ ] Set up uptime monitoring (UptimeRobot)
- [ ] Configure backup strategy
- [ ] Set up alerts for failures
