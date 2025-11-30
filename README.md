# MSDP Backend - Medical Surveillance & Disease Prediction System

A Django REST Framework backend for disease outbreak forecasting and surveillance, built with a modular monolithic architecture.

## 🏗️ Architecture Overview

This backend follows a **modular monolithic** approach where each feature exists as a separate Django app, but runs as a single deployed service. This balances simplicity with maintainability.

### Key Components

1. **Users App** (`apps/users/`)
   - JWT-based authentication
   - Role-based access control (Admin, Health Official, Lab Tech, Pharmacist)
   - User management

2. **Datasets App** (`apps/datasets/`)
   - File upload (CSV, Excel)
   - Data validation
   - Async processing with Celery

3. **Forecasting App** (`apps/forecasting/`)
   - ML model training
   - Disease outbreak predictions
   - Model versioning and registry

4. **Reports App** (`apps/reports/`)
   - Report generation (Excel, CSV, PDF)
   - Export functionality
   - Audit logging

### Technology Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL
- **Async Tasks**: Celery + Redis
- **ML Libraries**: scikit-learn, pandas, numpy
- **Deployment**: Render/Railway (Backend), Neon/ElephantSQL (DB), Redis Cloud

## 📁 Project Structure

```
MSDP-backend/
├── config/                 # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # URL routing
│   ├── celery.py          # Celery configuration
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point
├── apps/                   # Modular Django apps
│   ├── users/             # Authentication & user management
│   ├── datasets/          # File uploads & validation
│   ├── forecasting/       # ML models & predictions
│   └── reports/           # Report generation & export
├── storage/               # ML model storage
│   └── model_registry/    # Trained models (.joblib files)
├── media/                 # User uploads
├── staticfiles/           # Static files (CSS, JS)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (create from .env.example)
```

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.10+
- PostgreSQL (or use SQLite for development)
- Redis (for Celery)

### Step 1: Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Or on Linux/Mac
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set your values:
# - SECRET_KEY (generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - DATABASE_URL (PostgreSQL connection string)
# - REDIS_URL (Redis connection string)
```

### Step 4: Run Migrations

```bash
# Create database tables
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

### Step 5: Start Development Server

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker (for async tasks)
celery -A config worker -l info

# Terminal 3: Celery beat (for scheduled tasks)
celery -A config beat -l info
```

The API will be available at `http://localhost:8000/`

## 🔐 API Endpoints

### Authentication

- `POST /api/users/register/` - Create new account
- `POST /api/users/login/` - Login (get JWT tokens)
- `POST /api/users/refresh/` - Refresh access token
- `GET /api/users/profile/` - Get current user profile

### Datasets

- `GET /api/datasets/` - List all datasets
- `POST /api/datasets/` - Upload new dataset
- `GET /api/datasets/{id}/` - Get dataset details
- `DELETE /api/datasets/{id}/` - Delete dataset

### Forecasting

- `GET /api/forecasting/models/` - List ML models
- `POST /api/forecasting/models/` - Train new model
- `GET /api/forecasting/forecasts/` - List forecasts
- `POST /api/forecasting/forecasts/` - Generate forecast

### Reports

- `GET /api/reports/` - List reports
- `POST /api/reports/` - Generate new report
- `GET /api/reports/{id}/download/` - Download report

## 📚 Learning Resources

### For Beginners

1. **Django Basics**
   - [Official Django Tutorial](https://docs.djangoproject.com/en/5.0/intro/)
   - [Django Girls Tutorial](https://tutorial.djangogirls.org/)

2. **Django REST Framework**
   - [DRF Tutorial](https://www.django-rest-framework.org/tutorial/quickstart/)
   - [Serializers Explained](https://www.django-rest-framework.org/api-guide/serializers/)

3. **Celery (Async Tasks)**
   - [Celery Basics](https://docs.celeryq.dev/en/stable/getting-started/introduction.html)
   - [Django + Celery Tutorial](https://realpython.com/asynchronous-tasks-with-django-and-celery/)

4. **JWT Authentication**
   - [JWT Explained](https://jwt.io/introduction)
   - [DRF SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)

### Understanding the Code

Each file has extensive comments explaining:
- What it does
- Why it's structured that way
- Key concepts for learning

Start by reading:
1. `config/settings.py` - Main configuration
2. `apps/users/models.py` - Custom user model
3. `apps/users/views.py` - API endpoints
4. `apps/datasets/tasks.py` - Async task example

## 🧪 Testing the API

### Using cURL

```bash
# Register new user
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "role": "HEALTH_OFFICIAL"
  }'

# Login
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123"
  }'

# Use the access token from login response
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using Postman or Insomnia

1. Import the endpoints from above
2. Set Authorization header: `Bearer <your_access_token>`
3. Test each endpoint

## 🔧 Development Workflow

### Making Changes

1. **Add new feature**: Create new app with `python manage.py startapp app_name`
2. **Add new model**: Edit `models.py`, then run `python manage.py makemigrations` and `python manage.py migrate`
3. **Add new API endpoint**: Create view in `views.py`, add URL in `urls.py`
4. **Add async task**: Create function in `tasks.py` with `@shared_task` decorator

### Database Migrations

```bash
# After changing models.py
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View SQL for migration
python manage.py sqlmigrate app_name migration_number
```

## 🚢 Deployment Guide

See `DEPLOYMENT.md` for detailed deployment instructions.

### Quick Deploy Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Set strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Configure Redis for Celery
- [ ] Set `ALLOWED_HOSTS`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Run migrations on production DB
- [ ] Start Celery worker and beat

## 🤝 Connecting to Frontend

The React frontend (Next.js) connects to this backend via REST API calls.

1. **Set CORS**: Already configured in `settings.py`
2. **API Base URL**: Set in frontend `.env` as `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. **Authentication**: Frontend stores JWT token in localStorage/cookies

Example frontend API call:

```javascript
// Login example
const response = await fetch('http://localhost:8000/api/users/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});
const data = await response.json();
localStorage.setItem('access_token', data.tokens.access);
```

## 📝 Common Tasks

### Create Admin User

```bash
python manage.py createsuperuser
```

### Access Admin Interface

Visit `http://localhost:8000/admin/` and login with superuser credentials.

### Clear Celery Tasks

```bash
celery -A config purge
```

### Reset Database

```bash
python manage.py flush
```

## 🐛 Troubleshooting

### ModuleNotFoundError: No module named 'apps'

Make sure you're in the project root directory and virtual environment is activated.

### Celery not picking up tasks

Restart the Celery worker after adding new tasks.

### Database connection error

Check `DATABASE_URL` in `.env` file and ensure PostgreSQL is running.

## 📄 License

This project is for educational purposes (FYP).

## 👨‍💻 Author

Built as part of Final Year Project (FYP) to learn:
- Django backend development
- REST API design
- Async task processing
- ML integration
- Cloud deployment
