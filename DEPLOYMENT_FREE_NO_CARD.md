# FREE Deployment Guide (NO CREDIT CARD REQUIRED)

## 🎯 Best Options for Pakistan (No Card Needed)

### Option 1: PythonAnywhere ⭐ RECOMMENDED
- ✅ **Completely FREE** - No card ever required
- ✅ **PostgreSQL/MySQL included**
- ✅ **Perfect for Django**
- ✅ **512MB storage**
- ❌ No Redis/Celery (use scheduled tasks instead)

### Option 2: Railway.app
- ✅ **$5 free credit** (~500 hours)
- ✅ **No card for trial**
- ✅ **Full Celery + Redis support**
- ❌ Card required after credit expires

### Option 3: Vercel (Serverless Python)
- ✅ **Completely FREE**
- ✅ **No card required**
- ❌ Limited to serverless functions (no Celery)

---

## 🚀 OPTION 1: PythonAnywhere (BEST FOR YOU)

### Step 1: Create Account

1. Go to **https://www.pythonanywhere.com**
2. Click **"Pricing & signup"**
3. Choose **"Create a Beginner account"**
4. **NO CREDIT CARD** - just email verification
5. Login

### Step 2: Upload Code

1. Click **"Consoles"** tab
2. Click **"Bash"**
3. In the terminal:

```bash
# Clone your repository (push to GitHub first)
git clone https://github.com/YOUR_USERNAME/MSDP-backend.git
cd MSDP-backend
```

### Step 3: Create Virtual Environment

```bash
# Create virtualenv with Python 3.10
mkvirtualenv --python=/usr/bin/python3.10 msdp

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Setup Database

1. Go to **"Databases"** tab
2. Click **"Initialize PostgreSQL"** (FREE 100MB)
3. Note the connection details shown
4. Create `.env` file:

```bash
cd ~/MSDP-backend
nano .env
```

Add these lines (replace with your values):
```env
SECRET_KEY=generate-using-command-below
DEBUG=False
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
FRONTEND_URL=https://your-vercel-app.vercel.app
DATABASE_URL=postgresql://YOUR_USERNAME:PASSWORD@YOUR_USERNAME-xxxx.postgres.pythonanywhere-services.com/YOUR_USERNAME$msdp
```

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Step 5: Run Migrations

```bash
workon msdp
cd ~/MSDP-backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Step 6: Configure Web App

1. Go to **"Web"** tab
2. Click **"Add a new web app"**
3. Click **"Next"** (accept default domain)
4. Choose **"Manual configuration"**
5. Choose **"Python 3.10"**
6. Click **"Next"**

#### Configure WSGI File:

1. Click on **WSGI configuration file** link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
2. **DELETE ALL CONTENT**
3. Replace with:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/YOUR_USERNAME/MSDP-backend'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Replace `YOUR_USERNAME` with your actual PythonAnywhere username!**

#### Configure Virtual Environment:

1. Scroll to **"Virtualenv"** section
2. Enter: `/home/YOUR_USERNAME/.virtualenvs/msdp`
3. Click checkmark to save

#### Configure Static Files:

1. Scroll to **"Static files"** section
2. Add new entry:
   - **URL**: `/static/`
   - **Directory**: `/home/YOUR_USERNAME/MSDP-backend/staticfiles`
3. Click checkmark to save

### Step 7: Deploy!

1. Click **"Reload YOUR_USERNAME.pythonanywhere.com"** button
2. Check for errors in the **Error log** link
3. Visit: `https://YOUR_USERNAME.pythonanywhere.com/admin`

### Step 8: Setup Scheduled Training (Replaces Celery)

Since free tier doesn't have Celery, use **scheduled tasks**:

#### Create Management Command:

```bash
cd ~/MSDP-backend
mkdir -p apps/forecasting/management/commands
nano apps/forecasting/management/commands/run_pending_training.py
```

Add this code:
```python
from django.core.management.base import BaseCommand
from apps.forecasting.models import TrainingSession
from apps.forecasting.tasks import train_custom_model

class Command(BaseCommand):
    help = 'Process pending training sessions'

    def handle(self, *args, **options):
        pending = TrainingSession.objects.filter(status='PENDING')
        self.stdout.write(f'Found {pending.count()} pending sessions')
        
        for session in pending:
            self.stdout.write(f'Training session {session.id}...')
            try:
                train_custom_model(session.id)
                self.stdout.write(self.style.SUCCESS(f'✓ Session {session.id} completed'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Session {session.id} failed: {e}'))
```

Create `__init__.py`:
```bash
touch apps/forecasting/management/__init__.py
touch apps/forecasting/management/commands/__init__.py
```

#### Schedule the Task:

1. Go to **"Tasks"** tab
2. In **"Scheduled tasks"** section, add:
   - **Time**: `03:00` (3 AM UTC daily)
   - **Command**: `/home/YOUR_USERNAME/.virtualenvs/msdp/bin/python /home/YOUR_USERNAME/MSDP-backend/manage.py run_pending_training`
3. Click **"Create"**

### Step 9: Update Vercel Frontend

1. Go to **Vercel dashboard**
2. Select your MSDP project
3. **Settings** → **Environment Variables**
4. Update:
   ```
   NEXT_PUBLIC_API_URL=https://YOUR_USERNAME.pythonanywhere.com
   ```
5. **Redeploy** frontend

---

## 🚀 OPTION 2: Railway.app (If You Need Celery)

Railway gives you $5 free credit (no card needed) which equals ~500 hours of usage.

### Step 1: Sign Up

1. Go to **https://railway.app**
2. Click **"Login"** → **"Login with GitHub"**
3. **No credit card required** - you get $5 free

### Step 2: Create Project

1. Click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. Select **MSDP-backend** repository
4. Railway auto-detects Python and uses your `Procfile`

### Step 3: Add Database

1. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway automatically creates `DATABASE_URL` variable

### Step 4: Add Redis

1. Click **"New"** → **"Database"** → **"Add Redis"**
2. Railway automatically creates `REDIS_URL` variable

### Step 5: Add Environment Variables

Click your service → **"Variables"** tab:

```env
SECRET_KEY=your-generated-secret-key
DEBUG=False
FRONTEND_URL=https://your-vercel-app.vercel.app
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
CELERY_TASK_ALWAYS_EAGER=False
```

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Step 6: Deploy

Railway auto-deploys. Check the **"Deployments"** tab for progress.

Your URL: `https://your-service.up.railway.app`

### Step 7: Add Celery Worker

1. Click **"New"** → **"Empty Service"**
2. Link to same GitHub repo
3. In **"Settings"**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A config worker --loglevel=info --pool=solo`
4. Add same environment variables

---

## 🚀 OPTION 3: Vercel Serverless (Simplest, Limited)

Good for simple Django APIs without background tasks.

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Create `vercel.json`

```json
{
  "builds": [
    {
      "src": "config/wsgi.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "config/wsgi.py"
    }
  ]
}
```

### Step 3: Deploy

```bash
cd d:/Github/MSDP-backend
vercel
```

**Limitations**: No Celery, no long-running tasks, 10s execution limit

---

## 📊 Comparison Table

| Feature | PythonAnywhere | Railway | Vercel |
|---------|---------------|---------|--------|
| **Card Required** | ❌ Never | ❌ Not for trial | ❌ Never |
| **Free Tier** | ✅ Forever | ✅ $5 credit | ✅ Forever |
| **PostgreSQL** | ✅ 100MB | ✅ 1GB | ❌ Need external |
| **Celery** | ❌ Use cron | ✅ Full support | ❌ No |
| **Setup Difficulty** | Medium | Easy | Hard |
| **Best For** | Django apps | Full-stack | Simple APIs |

---

## ✅ Recommended Path

**For Pakistan (No Card Available):**
1. ✅ Use **PythonAnywhere** (main recommendation)
2. Replace Celery with daily scheduled tasks
3. Good enough for demo/MVP
4. Can upgrade later when card available

**If You Can Get $5 Credit:**
1. ✅ Use **Railway** for full Celery support
2. Lasts ~500 hours (about 20 days of continuous usage)
3. Perfect for testing before getting paid tier

---

## 🐛 Troubleshooting PythonAnywhere

### Error: "No module named 'dotenv'"

```bash
workon msdp
pip install python-dotenv
```

Then reload web app.

### Error: "DisallowedHost"

Check `.env` file has correct:
```
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
```

### Static Files Not Loading

```bash
cd ~/MSDP-backend
workon msdp
python manage.py collectstatic --noinput
```

Click **Reload** in Web tab.

### Database Connection Error

Verify `DATABASE_URL` in `.env` matches exactly what's shown in Databases tab.

---

## 📞 Next Steps

1. **Push code to GitHub** (if not already done)
2. **Choose deployment option** (PythonAnywhere recommended)
3. **Follow steps above**
4. **Update Vercel with backend URL**
5. **Test API endpoints**
6. **Upload initial data via Django admin**

Good luck! 🚀
