# API Testing Guide

## Quick Start Testing

### 1. Start the servers

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat
celery -A config beat -l info
```

### 2. Test Authentication Flow

#### Register a new user

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "Admin123!",
    "password_confirm": "Admin123!",
    "first_name": "Admin",
    "last_name": "User",
    "role": "ADMIN",
    "organization": "Health Department"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

Save the `access` token - you'll need it for authenticated requests!

#### Get profile

```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Test Dataset Upload

Create a sample CSV file (`test_data.csv`):
```csv
date,region,disease,cases
2024-01-01,North,Flu,150
2024-01-02,North,Flu,175
2024-01-03,North,Flu,200
```

Upload it:
```bash
curl -X POST http://localhost:8000/api/datasets/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "name=Test Dataset" \
  -F "description=Sample flu data" \
  -F "file=@test_data.csv"
```

List datasets:
```bash
curl -X GET http://localhost:8000/api/datasets/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Test Model Training

```bash
curl -X POST http://localhost:8000/api/forecasting/models/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Flu Predictor",
    "version": "1.0",
    "algorithm": "RandomForest",
    "dataset": 1
  }'
```

Check model status:
```bash
curl -X GET http://localhost:8000/api/forecasting/models/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Test Report Generation

```bash
curl -X POST http://localhost:8000/api/reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Monthly Forecast Report",
    "report_type": "FORECAST",
    "format": "EXCEL",
    "parameters": {
      "date_from": "2024-01-01",
      "date_to": "2024-12-31"
    }
  }'
```

Download report:
```bash
curl -X GET http://localhost:8000/api/reports/1/download/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output report.xlsx
```

## Using Postman/Insomnia

### Collection Setup

1. **Create Environment**
   - `base_url`: `http://localhost:8000`
   - `access_token`: (set after login)

2. **Authentication**
   - Type: Bearer Token
   - Token: `{{access_token}}`

### Requests Collection

#### Auth
- POST `{{base_url}}/api/users/register/`
- POST `{{base_url}}/api/users/login/`
- GET `{{base_url}}/api/users/profile/`

#### Datasets
- GET `{{base_url}}/api/datasets/`
- POST `{{base_url}}/api/datasets/` (form-data with file)
- GET `{{base_url}}/api/datasets/{id}/`

#### Forecasting
- GET `{{base_url}}/api/forecasting/models/`
- POST `{{base_url}}/api/forecasting/models/`
- GET `{{base_url}}/api/forecasting/forecasts/`

#### Reports
- GET `{{base_url}}/api/reports/`
- POST `{{base_url}}/api/reports/`
- GET `{{base_url}}/api/reports/{id}/download/`

## Expected Response Codes

- `200 OK` - Successful GET request
- `201 Created` - Successful POST (created new resource)
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - No permission
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Server error

## Common Errors

### "Authentication credentials were not provided"
- Solution: Add `Authorization: Bearer {token}` header

### "Token is invalid or expired"
- Solution: Login again to get new token or use refresh endpoint

### "File upload too large"
- Solution: File must be under 10MB

### "Unsupported file format"
- Solution: Use only .csv, .xlsx, or .xls files
