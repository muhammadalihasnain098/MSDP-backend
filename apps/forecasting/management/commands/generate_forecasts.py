"""
Management Command: generate_forecasts

Generates disease forecasts using trained models with exact notebook logic.

Usage:
    python manage.py generate_forecasts
    python manage.py generate_forecasts --disease malaria
    python manage.py generate_forecasts --start 2024-10-01 --end 2024-12-31
"""

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.forecasting.models import ForecastModel, Forecast
from apps.forecasting.ml_models import (
    generate_malaria_forecast,
    generate_dengue_forecast,
    load_model,
    PREDICT_START_DATE,
    PREDICT_END_DATE,
)


class Command(BaseCommand):
    help = 'Generate forecasts using trained models (exact notebook prediction logic)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disease',
            type=str,
            choices=['malaria', 'dengue', 'all'],
            default='all',
            help='Which disease to forecast (default: all)'
        )
        
        parser.add_argument(
            '--start',
            type=str,
            default=PREDICT_START_DATE,
            help=f'Start date for forecast (default: {PREDICT_START_DATE})'
        )
        
        parser.add_argument(
            '--end',
            type=str,
            default=PREDICT_END_DATE,
            help=f'End date for forecast (default: {PREDICT_END_DATE})'
        )

    def handle(self, *args, **options):
        disease = options['disease']
        start_date = options['start']
        end_date = options['end']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('GENERATING DISEASE FORECASTS'))
        self.stdout.write(self.style.SUCCESS(f'Period: {start_date} to {end_date}'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        diseases_to_forecast = []
        
        if disease == 'all':
            diseases_to_forecast = ['MALARIA', 'DENGUE']
        else:
            diseases_to_forecast = [disease.upper()]
        
        for disease_name in diseases_to_forecast:
            self.generate_disease_forecast(disease_name, start_date, end_date)
        
        self.stdout.write('\n' + self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Forecast generation completed!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
    
    def generate_disease_forecast(self, disease_name, start_date, end_date):
        """Generate forecast for a specific disease"""
        self.stdout.write(f'\n{disease_name} Forecast:')
        self.stdout.write('-' * 40)
        
        # Get trained model
        try:
            model = ForecastModel.objects.get(disease=disease_name, status='TRAINED')
            self.stdout.write(f'  [i] Using model: {model.name} (ID: {model.id})')
        except ForecastModel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'  [X] No trained model found for {disease_name}'))
            self.stdout.write(f'  [i] Run: python manage.py train_models --disease {disease_name.lower()}')
            return
        
        # Load model
        try:
            rf_regressor, feature_cols, metrics = load_model(disease_name)
            self.stdout.write(f'  [OK] Model loaded successfully')
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'  [X] Model file not found: {e}'))
            return
        
        # Generate predictions using EXACT notebook logic
        self.stdout.write(f'  [...] Running recursive predictions...')
        
        try:
            if disease_name == 'MALARIA':
                df_results, mae = generate_malaria_forecast(
                    rf_regressor,
                    feature_cols,
                    start_date,
                    end_date
                )
            elif disease_name == 'DENGUE':
                df_results, mae = generate_dengue_forecast(
                    rf_regressor,
                    feature_cols,
                    start_date,
                    end_date
                )
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Unknown disease: {disease_name}'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'  [OK] Predictions generated!'))
            self.stdout.write(f'     - MAE: {mae:.2f} cases')
            self.stdout.write(f'     - Forecast days: {len(df_results)}')
            
            # Save forecasts to database
            self.save_forecasts(model, df_results, mae, disease_name)
            
            # Print sample results
            self.print_sample_results(df_results)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [X] Error generating forecast: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def save_forecasts(self, model, df_results, mae, disease_name):
        """Save forecast results to database"""
        self.stdout.write(f'  [...] Saving forecasts to database...')
        
        # Delete existing forecasts for this model and period
        Forecast.objects.filter(
            model=model,
            forecast_date__in=df_results['date'].tolist()
        ).delete()
        
        # Create new forecasts
        forecasts = []
        for _, row in df_results.iterrows():
            forecasts.append(Forecast(
                model=model,
                disease=disease_name,
                region='National',
                forecast_date=row['date'],
                predicted_cases=int(row['predicted_tests']),
                actual_cases=int(row['actual_tests']) if 'actual_tests' in row else None,
                confidence_interval={
                    'lower': max(0, int(row['predicted_tests']) - 10),
                    'upper': int(row['predicted_tests']) + 10,
                },
                metadata={
                    'mae': float(mae),
                    'method': 'Recursive RandomForest prediction (exact notebook logic)',
                }
            ))
        
        Forecast.objects.bulk_create(forecasts, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f'  [OK] Saved {len(forecasts)} forecasts'))
    
    def print_sample_results(self, df_results):
        """Print sample forecast results"""
        self.stdout.write(f'\n  Sample predictions (first 5 days):')
        self.stdout.write(f'  ' + '-' * 50)
        
        for i, row in df_results.head(5).iterrows():
            date_str = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
            pred = int(row['predicted_tests'])
            actual = int(row['actual_tests']) if 'actual_tests' in row else 'N/A'
            self.stdout.write(f'    {date_str}: Predicted={pred:3d}, Actual={actual}')
