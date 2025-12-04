"""
Quick script to generate forecasts from existing trained models
Run this on Railway: python generate_forecasts.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.forecasting.ml_models import load_model, generate_dengue_forecast, generate_malaria_forecast
from apps.forecasting.models import Forecast, ForecastModel
from django.contrib.auth import get_user_model
from django.db import transaction
import pandas as pd

User = get_user_model()

def generate_forecasts_for_disease(disease, forecast_start, forecast_end):
    """Generate and save forecasts for a disease"""
    print(f"\n{'='*60}")
    print(f"Generating {disease} forecasts from {forecast_start} to {forecast_end}")
    print(f"{'='*60}\n")
    
    try:
        # Load existing model
        print(f"Loading {disease} model...")
        model_data = load_model(disease)
        regressor = model_data['regressor']
        feature_cols = model_data['feature_cols']
        print(f"✓ Model loaded. Features: {len(feature_cols)} columns")
        
        # Generate forecasts
        print(f"Generating forecasts...")
        if disease == 'DENGUE':
            forecasts_df, mae = generate_dengue_forecast(
                regressor, feature_cols, forecast_start, forecast_end
            )
        elif disease == 'MALARIA':
            forecasts_df, mae = generate_malaria_forecast(
                regressor, feature_cols, forecast_start, forecast_end
            )
        else:
            print(f"✗ Unknown disease: {disease}")
            return
        
        print(f"✓ Generated {len(forecasts_df)} forecasts")
        print(f"  MAE: {mae}")
        print(f"\nFirst 5 forecasts:")
        print(forecasts_df.head())
        
        # Get or create forecast model record
        forecast_model, created = ForecastModel.objects.get_or_create(
            name=f'{disease.lower()}_model',
            version='1.0',
            defaults={
                'algorithm': 'RandomForest',
                'disease': disease,
                'status': 'TRAINED',
            }
        )
        print(f"✓ ForecastModel {'created' if created else 'found'}: {forecast_model}")
        
        # Get admin user (or None)
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Save forecasts to database
        print(f"\nSaving forecasts to database...")
        forecast_count = 0
        
        with transaction.atomic():
            # Clear old forecasts for this disease
            deleted_count = Forecast.objects.filter(disease=disease).delete()[0]
            print(f"✓ Deleted {deleted_count} old {disease} forecasts")
            
            for idx, row in forecasts_df.iterrows():
                Forecast.objects.create(
                    model=forecast_model,
                    disease=disease,
                    region='Pakistan',
                    forecast_date=row['date'],
                    predicted_cases=int(row['predicted_tests']),
                    actual_cases=int(row['actual_tests']) if (pd.notna(row['actual_tests']) and row['actual_tests'] != -1) else None,
                    confidence_interval={},
                    metadata={'mae': mae} if mae else {},
                    created_by=admin_user
                )
                forecast_count += 1
                
                if forecast_count % 10 == 0:
                    print(f"  Saved {forecast_count}/{len(forecasts_df)} forecasts...")
        
        print(f"✓ Successfully saved {forecast_count} forecasts")
        
        # Verify
        saved_count = Forecast.objects.filter(disease=disease).count()
        print(f"✓ Verification: {saved_count} {disease} forecasts in database")
        
        return forecast_count
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == '__main__':
    print("="*60)
    print("FORECAST GENERATION SCRIPT")
    print("="*60)
    
    # Generate forecasts for next 60 days
    from datetime import datetime, timedelta
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=60)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    # Generate for both diseases
    dengue_count = generate_forecasts_for_disease('DENGUE', start_str, end_str)
    malaria_count = generate_forecasts_for_disease('MALARIA', start_str, end_str)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"DENGUE forecasts: {dengue_count}")
    print(f"MALARIA forecasts: {malaria_count}")
    print(f"Total: {dengue_count + malaria_count}")
    print(f"{'='*60}\n")
