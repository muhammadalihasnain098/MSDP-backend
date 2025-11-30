"""
Management Command: train_models

Trains both malaria and dengue models using exact notebook code.

Usage:
    python manage.py train_models
    python manage.py train_models --disease malaria
    python manage.py train_models --disease dengue
"""

from django.core.management.base import BaseCommand
from apps.forecasting.models import ForecastModel
from apps.forecasting.tasks import train_model as train_model_task


class Command(BaseCommand):
    help = 'Train disease forecasting models using exact notebook logic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disease',
            type=str,
            choices=['malaria', 'dengue', 'all'],
            default='all',
            help='Which disease model to train (default: all)'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run training as async Celery task (requires Redis/Celery running)'
        )

    def handle(self, *args, **options):
        disease = options['disease']
        use_async = options['async']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('TRAINING DISEASE FORECASTING MODELS'))
        self.stdout.write(self.style.SUCCESS('Using EXACT code from Jupyter notebooks'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        diseases_to_train = []
        
        if disease == 'all':
            diseases_to_train = ['MALARIA', 'DENGUE']
        else:
            diseases_to_train = [disease.upper()]
        
        for disease_name in diseases_to_train:
            self.train_disease_model(disease_name, use_async)
        
        self.stdout.write('\n' + self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Training completed!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        self.print_usage_instructions()
    
    def train_disease_model(self, disease_name, use_async):
        """Train a specific disease model"""
        self.stdout.write(f'\n{disease_name} Model Training:')
        self.stdout.write('-' * 40)
        
        # Create or get model record
        model, created = ForecastModel.objects.get_or_create(
            name=f'{disease_name} Forecasting Model',
            disease=disease_name,
            defaults={
                'version': '1.0',
                'description': f'Random Forest model trained with EXACT code from model_{"1" if disease_name == "MALARIA" else "2"}.ipynb',
                'algorithm': 'RandomForest',
                'status': 'PENDING',
            }
        )
        
        if not created:
            # Update existing model
            model.status = 'PENDING'
            model.save()
            self.stdout.write(f'  ℹ Using existing model: {model.name} (ID: {model.id})')
        else:
            self.stdout.write(f'  ✓ Created new model: {model.name} (ID: {model.id})')
        
        if use_async:
            # Run as Celery task
            self.stdout.write('  ⏳ Starting async training task...')
            result = train_model_task.delay(model.id)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Task queued: {result.id}'))
            self.stdout.write(f'  ℹ Check task status with: celery -A config inspect active')
        else:
            # Run synchronously
            self.stdout.write('  ⏳ Training model (this may take a minute)...')
            
            try:
                result = train_model_task(model.id)
                
                if result['status'] == 'success':
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Training completed!'))
                    self.stdout.write(f"     - Training MAE: {result['train_mae']:.2f}")
                    self.stdout.write(f"     - Training samples: {result['train_samples']}")
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ Training failed: {result["message"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
    
    def print_usage_instructions(self):
        """Print instructions for using the trained models"""
        self.stdout.write('\n' + 'Next Steps:')
        self.stdout.write('-' * 40)
        self.stdout.write('1. Verify models in database:')
        self.stdout.write('   python manage.py shell')
        self.stdout.write('   >>> from apps.forecasting.models import ForecastModel')
        self.stdout.write('   >>> ForecastModel.objects.filter(status="TRAINED")')
        self.stdout.write('')
        self.stdout.write('2. Generate forecasts:')
        self.stdout.write('   python manage.py generate_forecasts')
        self.stdout.write('')
        self.stdout.write('3. Access via API:')
        self.stdout.write('   GET http://localhost:8000/api/forecasting/models/')
        self.stdout.write('   GET http://localhost:8000/api/forecasting/forecasts/')
        self.stdout.write('')
