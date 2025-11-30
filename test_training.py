import os, django, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.forecasting.models import TrainingSession
from apps.forecasting.tasks import train_custom_model

# Get a failed session
session = TrainingSession.objects.get(id=4)
print(f"Testing session {session.id}: {session.disease}")
print(f"Training: {session.training_start_date} to {session.training_end_date}")
print(f"Forecast: {session.forecast_start_date} to {session.forecast_end_date}")
print("\n" + "="*80)
print("RUNNING TRAINING...")
print("="*80 + "\n")

try:
    result = train_custom_model(session.id)
    print(f"\n✓ SUCCESS: {result}")
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
