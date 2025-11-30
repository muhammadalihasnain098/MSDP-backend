# CONTRIBUTING.md

# Contributing to MSDP Backend

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/MSDP-backend.git
   cd MSDP-backend
   ```

2. **Run Setup Script**
   ```bash
   # Windows
   .\setup.ps1
   
   # Linux/Mac
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style

### Python Style Guide
- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names

### Django Best Practices
- Keep views thin, models fat
- Use serializers for validation
- Document all models and views
- Write tests for new features

### Naming Conventions
- Models: `PascalCase` (e.g., `ForecastModel`)
- Functions/Variables: `snake_case` (e.g., `validate_dataset`)
- Constants: `UPPER_CASE` (e.g., `MAX_UPLOAD_SIZE`)

## Adding New Features

### 1. Create New Model

```python
# apps/your_app/models.py
class YourModel(models.Model):
    """
    Brief description
    
    Detailed explanation of what this model represents.
    """
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
```

### 2. Create Serializer

```python
# apps/your_app/serializers.py
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    """Serializer for YourModel"""
    
    class Meta:
        model = YourModel
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']
```

### 3. Create View

```python
# apps/your_app/views.py
from rest_framework import viewsets
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    """API endpoints for YourModel"""
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
```

### 4. Add URLs

```python
# apps/your_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r'', YourModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

### 5. Register in Admin

```python
# apps/your_app/admin.py
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
```

### 6. Create Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

## Testing

### Run Tests
```bash
python manage.py test
```

### Write Tests
```python
# apps/your_app/tests.py
from django.test import TestCase
from .models import YourModel

class YourModelTestCase(TestCase):
    def setUp(self):
        YourModel.objects.create(name="Test")
    
    def test_model_creation(self):
        obj = YourModel.objects.get(name="Test")
        self.assertEqual(obj.name, "Test")
```

## Commit Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```
feat(users): add password reset functionality

- Add password reset endpoint
- Send reset email via Celery
- Add reset token validation

Closes #123
```

```
fix(datasets): handle missing file error

Fixed bug where missing file caused server crash

Fixes #456
```

## Pull Request Process

1. **Update Documentation**
   - Update README if needed
   - Add docstrings to new code
   - Update API_TESTING.md if adding endpoints

2. **Test Your Changes**
   ```bash
   python manage.py test
   python manage.py check
   ```

3. **Create Pull Request**
   - Describe what changed
   - Reference related issues
   - Include screenshots if UI changes

4. **Code Review**
   - Address review comments
   - Keep discussion respectful

## Project Structure Rules

### Where to Put Code

- **Models**: `apps/<app_name>/models.py`
- **Views**: `apps/<app_name>/views.py`
- **Serializers**: `apps/<app_name>/serializers.py`
- **URLs**: `apps/<app_name>/urls.py`
- **Tasks**: `apps/<app_name>/tasks.py`
- **Utils**: `apps/<app_name>/utils.py`
- **Tests**: `apps/<app_name>/tests.py`

### Don't
- Don't put business logic in views
- Don't hardcode values
- Don't commit `.env` file
- Don't commit `db.sqlite3`
- Don't commit `media/` or `storage/` files

## Getting Help

- **Documentation**: Check README.md and ARCHITECTURE.md
- **Issues**: Search existing issues before creating new ones
- **Questions**: Open a discussion on GitHub

## License

By contributing, you agree that your contributions will be licensed under the project's license.
