# Architecture & Learning Guide

## 🏛️ System Architecture

### High-Level Overview

```
┌─────────────────┐
│  React Frontend │ (Next.js on Vercel)
│  (Port 3000)    │
└────────┬────────┘
         │ REST API (JWT)
         │
┌────────▼────────────────────────────────────┐
│         Django Backend (Render.com)         │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Users   │  │ Datasets │  │Forecast  │ │
│  │   App    │  │   App    │  │   App    │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                             │
│  ┌──────────┐  ┌──────────┐               │
│  │ Reports  │  │  Celery  │               │
│  │   App    │  │  Tasks   │               │
│  └──────────┘  └──────────┘               │
└──────┬──────────────┬──────────────────────┘
       │              │
       │              │
┌──────▼──────┐  ┌───▼────────┐
│ PostgreSQL  │  │   Redis    │
│  (Neon)     │  │ (Upstash)  │
└─────────────┘  └────────────┘
```

## 📚 Django Concepts Explained

### 1. Apps (Modular Architecture)

**What is an App?**
An app is a self-contained module that handles one specific feature.

**Why Multiple Apps?**
- **Separation of Concerns**: Each app has one responsibility
- **Reusability**: Apps can be reused in other projects
- **Maintainability**: Easier to understand and modify
- **Scalability**: Can split into microservices later if needed

**Example:**
```python
# apps/users/ handles ONLY user-related functionality
# apps/forecasting/ handles ONLY ML and predictions
# They don't interfere with each other
```

### 2. Models (Database Tables)

**What are Models?**
Python classes that represent database tables.

**Example:**
```python
class User(AbstractUser):
    role = models.CharField(max_length=20)
    # ↓ This becomes a database column
    # Table: users_user
    # Column: role (VARCHAR(20))
```

**Key Concepts:**
- **Fields**: Columns in the table (CharField, IntegerField, etc.)
- **Relationships**: ForeignKey (one-to-many), ManyToMany
- **Migrations**: Convert model changes to SQL

### 3. Serializers (Data Conversion)

**What are Serializers?**
Convert Python objects to JSON (and vice versa).

**Example:**
```python
# Python object (from database)
user = User.objects.get(id=1)

# Serializer converts to JSON
serializer = UserSerializer(user)
# Output: {"id": 1, "username": "john", "email": "john@example.com"}
```

**Why Needed?**
- **Validation**: Ensure data is correct before saving
- **Format**: Control what data is sent to API
- **Security**: Hide sensitive fields (like passwords)

### 4. Views (API Endpoints)

**What are Views?**
Functions/classes that handle HTTP requests.

**Example Flow:**
```
Client sends:     POST /api/users/login/
                  ↓
Django routes to: LoginView.post()
                  ↓
View processes:   - Check credentials
                  - Generate JWT token
                  ↓
View returns:     JSON response with token
```

**Types of Views:**
- **APIView**: Basic class-based view
- **ViewSet**: Automatic CRUD operations
- **@api_view**: Function-based view

### 5. URLs (Routing)

**What is URL Routing?**
Maps URL patterns to views.

**Example:**
```python
# URL: /api/users/login/
# ↓ Maps to ↓
path('login/', LoginView.as_view())
# ↓ Calls ↓
LoginView.post(request)
```

### 6. Authentication (JWT)

**What is JWT?**
JSON Web Token - a secure way to authenticate API requests.

**Flow:**
```
1. User logs in
   ↓
2. Server generates JWT token
   {
     "user_id": 1,
     "exp": "2024-12-31",
     "signature": "..."
   }
   ↓
3. Client stores token
   ↓
4. Client sends token with each request
   Header: "Authorization: Bearer eyJ0eXAi..."
   ↓
5. Server verifies token and identifies user
```

**Why JWT over Sessions?**
- **Stateless**: Server doesn't store session data
- **Scalable**: Works across multiple servers
- **Mobile-friendly**: Easy to use in mobile apps

## 🔄 Async Tasks with Celery

### What is Celery?

**Problem:**
Some tasks take too long (model training, file processing).
If done synchronously, API request times out.

**Solution:**
Celery processes tasks in background.

### Architecture

```
API Request → Queue Task → Return Immediately
                    ↓
              Celery Worker processes in background
                    ↓
              Update database when done
```

### Example

```python
# Without Celery (SLOW - blocks for minutes)
def upload_dataset(request):
    dataset = Dataset.objects.create(...)
    validate_data(dataset)  # Takes 5 minutes!
    train_model(dataset)    # Takes 30 minutes!
    return Response()  # User waits 35 minutes!

# With Celery (FAST - returns immediately)
def upload_dataset(request):
    dataset = Dataset.objects.create(...)
    validate_data.delay(dataset.id)  # Queue task
    return Response()  # Returns in 1 second!

# Celery worker processes task in background
@shared_task
def validate_data(dataset_id):
    # Runs separately from API request
    dataset = Dataset.objects.get(id=dataset_id)
    # ... validation logic ...
```

### Components

1. **Broker (Redis)**: Message queue
2. **Worker**: Processes tasks
3. **Beat**: Scheduler for periodic tasks
4. **Task**: Function to run asynchronously

## 🗃️ Database Relationships

### One-to-Many (ForeignKey)

```python
class Dataset(models.Model):
    uploaded_by = ForeignKey(User)
    # One user can upload many datasets
    # One dataset belongs to one user

# Query:
user.datasets.all()  # Get all datasets by this user
```

### Many-to-Many

```python
class Disease(models.Model):
    regions = ManyToManyField(Region)
    # One disease can affect many regions
    # One region can have many diseases

# Query:
disease.regions.all()  # Get all regions
region.disease_set.all()  # Get all diseases
```

## 🔐 Permissions & Roles

### Role-Based Access Control

```python
# User model has role field
class User(AbstractUser):
    role = models.CharField(
        choices=[
            ('ADMIN', 'Administrator'),
            ('HEALTH_OFFICIAL', 'Health Official'),
        ]
    )

# In views, check permissions
if request.user.role == 'ADMIN':
    # Allow admin-only actions
```

### Permission Classes

```python
class DatasetViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    # Only logged-in users can access
    
    def destroy(self, request, pk):
        # Only admins can delete
        if not request.user.is_admin():
            return Response(status=403)
```

## 🧪 Machine Learning Integration

### Model Training Pipeline

```
1. Upload Dataset (CSV/Excel)
   ↓
2. Validate Data (Celery Task)
   - Check columns
   - Check data types
   - Remove duplicates
   ↓
3. Train Model (Celery Task)
   - Split train/test
   - Train algorithm (RandomForest, etc.)
   - Evaluate accuracy
   ↓
4. Save Model (joblib file)
   - Store in storage/model_registry/
   - Save metadata in database
   ↓
5. Use for Predictions
   - Load trained model
   - Make forecasts
   - Return predictions via API
```

### Code Example

```python
# Train model (runs in background)
@shared_task
def train_model(model_id):
    model = ForecastModel.objects.get(id=model_id)
    
    # Load data
    df = pd.read_csv(model.dataset.file.path)
    
    # Prepare features
    X = df[['feature1', 'feature2']]
    y = df['target']
    
    # Train
    clf = RandomForestRegressor()
    clf.fit(X, y)
    
    # Save
    joblib.dump(clf, f'models/{model.name}.joblib')
    model.status = 'TRAINED'
    model.save()

# Use model for prediction
def predict(data):
    clf = joblib.load('models/model.joblib')
    prediction = clf.predict(data)
    return prediction
```

## 📊 API Design Patterns

### RESTful Principles

```
GET    /api/datasets/     - List all
POST   /api/datasets/     - Create new
GET    /api/datasets/1/   - Get specific
PUT    /api/datasets/1/   - Update
DELETE /api/datasets/1/   - Delete
```

### Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad request (validation error)
- **401**: Unauthorized (not logged in)
- **403**: Forbidden (no permission)
- **404**: Not found
- **500**: Server error

### Response Format

```json
{
  "id": 1,
  "name": "Dataset Name",
  "status": "VALID",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## 🎯 Best Practices

### 1. Keep Apps Small
One app = one feature

### 2. Use Serializers for Validation
Don't trust user input

### 3. Async for Slow Tasks
Use Celery for anything > 2 seconds

### 4. Proper Error Handling
Return meaningful error messages

### 5. Document Your Code
Use docstrings and comments

### 6. Security First
- Validate all input
- Use JWT tokens
- Never expose secrets
- Use HTTPS in production

## 📖 Further Learning

### Next Steps

1. **Read Django Docs**: [docs.djangoproject.com](https://docs.djangoproject.com)
2. **Build Features**: Add new endpoints, models
3. **Study Celery**: [docs.celeryq.dev](https://docs.celeryq.dev)
4. **Learn SQL**: Understand database queries
5. **Deploy**: Get real-world experience

### Recommended Path

1. Understand models & migrations
2. Create simple views
3. Add serializers
4. Implement authentication
5. Add async tasks
6. Deploy to production
7. Monitor & optimize

## 💡 Common Questions

**Q: Why Django over Flask/FastAPI?**
A: Django includes everything (ORM, admin, auth). Good for learning full stack.

**Q: Why PostgreSQL over SQLite?**
A: Production-ready, scalable, supports advanced features.

**Q: Why Celery over simple threading?**
A: Robust, scalable, distributed, handles failures.

**Q: How to add new feature?**
A: Create model → serializer → view → URL → test

**Q: How to debug?**
A: Use `print()`, Django shell, debugger, check logs
