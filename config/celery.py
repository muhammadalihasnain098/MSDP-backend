"""
Celery Configuration

This file configures Celery for asynchronous task processing.
Celery Worker processes background tasks (model training, data processing).
Celery Beat handles scheduled tasks (periodic forecasting).

For learning:
- Redis acts as the message broker (task queue)
- Tasks are defined in each app's tasks.py file
- Beat schedules can be managed via Django admin (django_celery_beat)
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('msdp_backend')

# Load configuration from Django settings (prefix: CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Example scheduled tasks (can also be configured in Django admin)
app.conf.beat_schedule = {
    # Example: Run forecasting every day at midnight
    'daily-forecasting': {
        'task': 'apps.forecasting.tasks.run_daily_forecast',
        'schedule': crontab(hour=0, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Example debug task"""
    print(f'Request: {self.request!r}')
