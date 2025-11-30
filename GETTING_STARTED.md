# GETTING STARTED - Complete Guide

Welcome! This guide will walk you through everything step-by-step.

## 📖 What You've Built

A complete Django REST API backend with:
- ✅ JWT Authentication
- ✅ User Management with Roles
- ✅ File Upload & Validation
- ✅ Machine Learning Model Training
- ✅ Disease Forecasting
- ✅ Report Generation
- ✅ Async Task Processing
- ✅ Production-Ready Deployment Config

## 🎯 Learning Path

### Week 1: Understand the Basics
1. **Read These Files (in order):**
   - `README.md` - Overview and quick start
   - `ARCHITECTURE.md` - How everything works
   - `config/settings.py` - Main configuration

2. **Understand Django Apps:**
   - `apps/users/` - Start here (authentication)
   - `apps/datasets/` - File handling
   - `apps/forecasting/` - ML integration
   - `apps/reports/` - Report generation

3. **Key Concepts to Learn:**
   - Models (database tables)
   - Serializers (data conversion)
   - Views (API endpoints)
   - URLs (routing)
   - JWT (authentication)

### Week 2: Set Up Locally
1. **Follow Quick Start:**
   ```bash
   # Run setup script
   .\setup.ps1
   
   # Start servers (3 terminals)
   python manage.py runserver
   celery -A config worker -l info
   celery -A config beat -l info
   ```

2. **Test the API:**
   - Follow `API_TESTING.md`
   - Use Postman/Insomnia
   - Test each endpoint

3. **Explore Admin Panel:**
   - Visit http://localhost:8000/admin/
   - Create users, view data
   - Understand the interface

### Week 3: Make Changes
1. **Small Changes:**
   - Add a field to User model
   - Create a new endpoint
   - Modify a serializer

2. **Understand Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Add a Feature:**
   - Follow `CONTRIBUTING.md`
   - Create a new model
   - Add CRUD endpoints

### Week 4: Deploy to Production
1. **Read `DEPLOYMENT.md`**
2. **Set up cloud services:**
   - PostgreSQL (Neon)
   - Redis (Upstash)
   - Backend (Render)
3. **Deploy and test**

## 🚀 Quick Start (TL;DR)

### Prerequisites
- Python 3.10+
- PostgreSQL (optional for dev)
- Redis (optional for dev)

### Installation

```bash
# 1. Navigate to backend directory
cd d:/Github/MSDP-backend

# 2. Run setup script
.\setup.ps1

# 3. Update .env file
# Edit DATABASE_URL and REDIS_URL if needed

# 4. Start Django (Terminal 1)
python manage.py runserver

# 5. Start Celery Worker (Terminal 2)
celery -A config worker -l info

# 6. Start Celery Beat (Terminal 3)
celery -A config beat -l info
```

### First API Call

```bash
# Create account
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!",
    "password_confirm": "Test123!",
    "role": "ADMIN"
  }'
```

## 📚 Documentation Index

| File | Purpose | When to Read |
|------|---------|--------------|
| `README.md` | Overview & setup | Start here |
| `ARCHITECTURE.md` | How it works | After setup |
| `API_TESTING.md` | Test endpoints | When testing |
| `DEPLOYMENT.md` | Deploy to cloud | Before deploying |
| `CONTRIBUTING.md` | Make changes | When developing |

## 🗺️ Project Structure Explained

```
MSDP-backend/
│
├── config/                 # Django settings
│   ├── settings.py        # ⭐ Main config - start here
│   ├── urls.py            # URL routing
│   ├── celery.py          # Async tasks config
│   └── wsgi.py            # Production server
│
├── apps/                   # Your features (modular apps)
│   │
│   ├── users/             # ⭐ Authentication - read this first
│   │   ├── models.py      # User model with roles
│   │   ├── serializers.py # Data validation
│   │   ├── views.py       # API endpoints (login, register)
│   │   ├── urls.py        # URL mapping
│   │   └── admin.py       # Admin interface
│   │
│   ├── datasets/          # File upload & validation
│   │   ├── models.py      # Dataset metadata
│   │   ├── views.py       # Upload endpoint
│   │   ├── tasks.py       # ⭐ Async validation (Celery)
│   │   └── serializers.py
│   │
│   ├── forecasting/       # ML models & predictions
│   │   ├── models.py      # Model registry
│   │   ├── tasks.py       # ⭐ Model training (Celery)
│   │   └── views.py       # Prediction endpoints
│   │
│   └── reports/           # Report generation
│       ├── models.py      # Report metadata
│       ├── tasks.py       # Generate reports
│       └── views.py       # Download endpoint
│
├── storage/               # ML models stored here
│   └── model_registry/    # .joblib files
│
├── media/                 # User uploads (created on first upload)
├── staticfiles/           # CSS, JS (created by collectstatic)
│
├── manage.py              # ⭐ Django command-line tool
├── requirements.txt       # Python dependencies
├── .env                   # ⭐ Your secrets (create from .env.example)
├── .env.example           # Template for environment variables
│
├── Procfile               # Deployment (Render/Heroku)
├── runtime.txt            # Python version
├── render.yaml            # Render config
│
└── Documentation/
    ├── README.md          # This file!
    ├── ARCHITECTURE.md    # How everything works
    ├── API_TESTING.md     # Test your API
    ├── DEPLOYMENT.md      # Deploy to production
    └── CONTRIBUTING.md    # Development guide
```

## 🎓 Learning Modules

### Module 1: Authentication (apps/users/)

**What you'll learn:**
- Custom User model
- JWT tokens
- Role-based access

**Read in order:**
1. `apps/users/models.py` - User model
2. `apps/users/serializers.py` - Data validation
3. `apps/users/views.py` - Login/register endpoints

**Try this:**
```bash
# Create user via API
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "Pass123!", "password_confirm": "Pass123!", "role": "ADMIN"}'
```

### Module 2: File Uploads (apps/datasets/)

**What you'll learn:**
- File uploads in Django
- Async processing with Celery
- Data validation

**Read in order:**
1. `apps/datasets/models.py` - Dataset model
2. `apps/datasets/views.py` - Upload endpoint
3. `apps/datasets/tasks.py` - ⭐ Celery tasks

**Try this:**
Create a CSV file and upload it via API.

### Module 3: ML Integration (apps/forecasting/)

**What you'll learn:**
- Training models asynchronously
- Saving/loading models
- Making predictions

**Read in order:**
1. `apps/forecasting/models.py` - Model registry
2. `apps/forecasting/tasks.py` - ⭐ Training logic
3. `apps/forecasting/views.py` - API endpoints

### Module 4: Reports (apps/reports/)

**What you'll learn:**
- Generating Excel/CSV
- File downloads
- Audit logging

**Read in order:**
1. `apps/reports/models.py`
2. `apps/reports/tasks.py`
3. `apps/reports/views.py`

## 🔧 Common Tasks

### Add New User
```bash
python manage.py createsuperuser
```

### View Database
```bash
python manage.py dbshell
```

### Django Shell (Interactive Python)
```bash
python manage.py shell

# Try:
>>> from apps.users.models import User
>>> User.objects.all()
>>> user = User.objects.create_user(username='test', password='pass')
```

### Check for Issues
```bash
python manage.py check
```

### View Migrations
```bash
python manage.py showmigrations
```

### Create Admin User
```bash
python manage.py createsuperuser
# Then visit: http://localhost:8000/admin/
```

## 🐛 Troubleshooting

### "No module named 'apps'"
**Solution:** Make sure you're in the right directory and virtual environment is activated.
```bash
cd d:/Github/MSDP-backend
.\venv\Scripts\Activate.ps1
```

### Database errors
**Solution:** Run migrations
```bash
python manage.py migrate
```

### Celery not working
**Solution:** Make sure Redis is running and REDIS_URL is correct in .env

### Import errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

## 🎯 Next Steps

### Immediate (Do Now)
1. ✅ Run `setup.ps1`
2. ✅ Start servers
3. ✅ Test with `API_TESTING.md`
4. ✅ Explore admin panel

### This Week
1. Read `ARCHITECTURE.md`
2. Understand each app
3. Make small changes
4. Add a new field to a model

### This Month
1. Add new feature
2. Write tests
3. Deploy to production
4. Connect frontend

## 📞 Getting Help

### Resources
- **Django Docs**: https://docs.djangoproject.com
- **DRF Docs**: https://www.django-rest-framework.org
- **Celery Docs**: https://docs.celeryq.dev

### Debugging
1. Check terminal output
2. Look at logs
3. Use Django shell
4. Add print statements
5. Use debugger (pdb)

### Common Questions

**Q: How do I add a new endpoint?**
A: Create view → add to urls.py → test

**Q: How do I change the database?**
A: Update DATABASE_URL in .env

**Q: How do I add a field to a model?**
A:
```python
# 1. Edit model
class User(AbstractUser):
    new_field = models.CharField(max_length=100)

# 2. Create migration
python manage.py makemigrations

# 3. Apply migration
python manage.py migrate
```

**Q: How do I test an endpoint?**
A: See `API_TESTING.md`

## 🎉 You're Ready!

You now have:
- ✅ Complete Django backend
- ✅ JWT authentication
- ✅ Async task processing
- ✅ ML integration
- ✅ Production deployment config
- ✅ Comprehensive documentation

**Start with:**
```bash
.\setup.ps1
```

**Then explore:**
- Django admin: http://localhost:8000/admin/
- API endpoints: See `API_TESTING.md`
- Code: Start with `apps/users/`

**Happy coding! 🚀**
