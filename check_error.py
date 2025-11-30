import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.forecasting.models import TrainingSession
for s in TrainingSession.objects.all().order_by('-created_at')[:5]:
    print(f'ID:{s.id} Status:{s.status} Disease:{s.disease} Train:{s.training_start_date} to {s.training_end_date} Forecast:{s.forecast_start_date} to {s.forecast_end_date}')
