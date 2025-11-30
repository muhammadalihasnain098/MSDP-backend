import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.forecasting.models import TrainingSession
from apps.users.models import User
admin = User.objects.filter(role='ADMIN').first()
session = TrainingSession.objects.create(
    disease='MALARIA',
    training_start_date='2023-01-01',
    training_end_date='2024-12-31',
    forecast_start_date='2025-01-01',
    forecast_end_date='2025-01-31',
    trained_by=admin
)
print(f'Created session {session.id}')
from apps.forecasting.tasks import train_custom_model
result = train_custom_model(session.id)
print(result)
