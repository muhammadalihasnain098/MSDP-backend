# How to Start Celery for Background Training

Celery allows training to run in the background while you use the application.

## Step 1: Start Redis (Message Broker)

Celery needs a message broker. Install and start Redis:

### Option A: Using Docker (Recommended)
```powershell
docker run -d -p 6379:6379 redis:alpine
```

### Option B: Using Windows Redis
Download from: https://github.com/microsoftarchive/redis/releases
Or install via Chocolatey:
```powershell
choco install redis-64
redis-server
```

## Step 2: Start Celery Worker

Open a **new terminal** (keep Django server running in another):

```powershell
cd D:\Github\MSDP-backend
.\venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo
```

**Note**: Use `--pool=solo` on Windows to avoid multiprocessing issues.

## Step 3: Use the Application

Now when you click "Train Model" in the admin interface:
1. Click button → Training session created instantly
2. Celery worker picks up the task in background
3. You can navigate away and do other things
4. Refresh the "Training History" section to see progress
5. Status will change: PENDING → TRAINING → COMPLETED

## Monitoring Training Progress

### In Celery Terminal
You'll see real-time logs:
```
[2024-11-30 18:30:00] Task forecasting.tasks.train_custom_model[abc123] received
[2024-11-30 18:30:05] Training malaria model...
[2024-11-30 18:30:08] Model trained! MAE: 0.34
[2024-11-30 18:30:10] Generating forecasts...
[2024-11-30 18:30:12] Task forecasting.tasks.train_custom_model[abc123] succeeded
```

### In Admin UI
Refresh the "Training History" section to see:
- Status changes (PENDING → TRAINING → COMPLETED)
- MAE score when completed
- Timestamp of completion

## How It Works

1. **Django Server** (Terminal 1): Handles web requests, creates TrainingSession
2. **Celery Worker** (Terminal 2): Executes background training tasks
3. **Redis**: Passes messages between Django and Celery

```
Browser → Django → Redis → Celery Worker
   ↓                           ↓
Database ← ← ← ← ← ← ← ← ← ← Training
```

## Troubleshooting

### Error: "Redis connection refused"
- Make sure Redis is running: `docker ps` or `redis-cli ping`
- Check CELERY_BROKER_URL in settings.py

### Error: "No module named celery"
```powershell
.\venv\Scripts\pip.exe install celery redis
```

### Training stays PENDING forever
- Check if Celery worker is running
- Look for errors in Celery terminal
- Check Redis connection

### On Windows: "OSError: [WinError 87]"
- Use `--pool=solo` flag when starting Celery worker
