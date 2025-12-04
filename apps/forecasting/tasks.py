"""
Forecasting Celery Tasks

Integrates the EXACT ML code from Jupyter notebooks (ml_models.py).

These tasks orchestrate:
1. Training models using notebook logic
2. Saving trained models to database
3. Generating forecasts with recursive prediction
4. Storing results for API consumption
"""

from celery import shared_task
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
import traceback

from .models import ForecastModel, Forecast, TrainingSession
from .ml_models import (
    train_malaria_model,
    train_dengue_model,
    generate_malaria_forecast,
    generate_dengue_forecast,
    save_model,
    load_model,
    PREDICT_START_DATE,
    PREDICT_END_DATE,
)


@shared_task
def train_custom_model(session_id):
    """
    Train ML model with custom date ranges from TrainingSession

    This task runs in the background via Celery, allowing the user
    to continue working while training completes.
    """
    print(f"==== TRAIN_CUSTOM_MODEL TASK STARTED for session_id={session_id} ====")
    try:
        session = TrainingSession.objects.get(id=session_id)
        print(f"Session found: disease={session.disease}, status={session.status}")

        # Update status to TRAINING
        session.status = 'TRAINING'
        session.save()

        # Extract parameters
        disease = session.disease
        training_start = session.training_start_date.strftime('%Y-%m-%d')
        training_end = session.training_end_date.strftime('%Y-%m-%d')
        forecast_start = session.forecast_start_date.strftime('%Y-%m-%d')
        forecast_end = session.forecast_end_date.strftime('%Y-%m-%d')

        print(f"Training parameters: disease={disease}, train={training_start} to {training_end}, forecast={forecast_start} to {forecast_end}")

        # Train the model with custom dates
        if disease == 'MALARIA':
            model, feature_cols, metrics = train_malaria_model(
                training_start=training_start,
                training_end=training_end,
                forecast_start=forecast_start,
                forecast_end=forecast_end
            )
        elif disease == 'DENGUE':
            model, feature_cols, metrics = train_dengue_model(
                training_start=training_start,
                training_end=training_end,
                forecast_start=forecast_start,
                forecast_end=forecast_end
            )
        else:
            raise ValueError(f'Unknown disease: {disease}')

        print(f"Model training complete! Metrics: {metrics}")

        # Save model to registry
        model_name = f'{disease.lower()}_model_custom_{session.id}'
        model_path = save_model(model, feature_cols, metrics, disease)

        # Create or get ForecastModel record
        forecast_model, created = ForecastModel.objects.get_or_create(
            name=model_name,
            version=f'custom_{session.id}',
            defaults={
                'algorithm': 'RandomForest',
                'disease': disease,
                'description': f'Custom training: {training_start} to {training_end}',
                'model_file': model_path,
                'trained_by': session.trained_by,
                'trained_at': timezone.now(),
                'status': 'TRAINED',
                'accuracy': metrics.get('train_mae'),
                'metrics': metrics
            }
        )

        # Link to session
        session.model = forecast_model
        session.mae_score = metrics['train_mae']
        session.trained_at = timezone.now()

        # Generate forecasts
        print(f"Starting forecast generation for {disease} from {forecast_start} to {forecast_end}")
        if disease == 'MALARIA':
            forecasts_df, forecast_mae = generate_malaria_forecast(
                model, feature_cols, forecast_start, forecast_end
            )
        else:
            forecasts_df, forecast_mae = generate_dengue_forecast(
                model, feature_cols, forecast_start, forecast_end
            )
        
        print(f"Forecast generation complete. Generated {len(forecasts_df)} forecasts")
        print(f"Forecast DataFrame columns: {forecasts_df.columns.tolist()}")
        print(f"First few forecasts:\n{forecasts_df.head()}")

        # Save forecasts to database
        forecast_count = 0
        for _, row in forecasts_df.iterrows():
            try:
                Forecast.objects.create(
                    model=forecast_model,
                    training_session=session,
                    disease=disease,
                    region='Pakistan',
                    forecast_date=row['date'],
                    predicted_cases=int(row['predicted_tests']),
                    actual_cases=int(row['actual_tests']) if pd.notna(row['actual_tests']) else None,
                    confidence_interval={},
                    metadata={'forecast_mae': forecast_mae} if forecast_mae else {},
                    created_by=session.trained_by
                )
                forecast_count += 1
            except Exception as forecast_err:
                print(f"Error saving forecast for {row['date']}: {forecast_err}")
                continue
        
        print(f"Successfully saved {forecast_count} forecasts to database")

        # Update session status
        session.status = 'COMPLETED'
        session.metadata = {
            'forecast_count': forecast_count,
            'model_path': model_path,
            'metrics': metrics
        }
        session.save()

        return {
            'status': 'success',
            'session_id': session_id,
            'disease': disease,
            'train_mae': metrics['train_mae'],
            'forecast_count': forecast_count,
        }

    except Exception as e:
        # Update session status to FAILED
        session = TrainingSession.objects.get(id=session_id)
        session.status = 'FAILED'
        session.metadata = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        session.save()

        return {
            'status': 'error',
            'session_id': session_id,
            'message': str(e),
            'traceback': traceback.format_exc()
        }
