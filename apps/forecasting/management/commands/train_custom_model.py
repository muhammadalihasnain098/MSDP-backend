"""
Management command to train models with custom date ranges from TrainingSession
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.forecasting.models import TrainingSession, ForecastModel, Forecast
from apps.forecasting.ml_models import (
    train_malaria_model,
    train_dengue_model,
    generate_malaria_forecast,
    generate_dengue_forecast,
    save_model,
)
import traceback


class Command(BaseCommand):
    help = 'Train model with custom date ranges from TrainingSession'

    def add_arguments(self, parser):
        parser.add_argument(
            'session_id',
            type=int,
            help='TrainingSession ID to execute'
        )

    def handle(self, *args, **options):
        session_id = options['session_id']
        
        try:
            session = TrainingSession.objects.get(id=session_id)
        except TrainingSession.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'TrainingSession {session_id} not found'))
            return

        self.stdout.write(f'Starting training for session {session_id}: {session.disease}')
        self.stdout.write(f'Training: {session.training_start_date} to {session.training_end_date}')
        self.stdout.write(f'Forecast: {session.forecast_start_date} to {session.forecast_end_date}')

        # Update status to TRAINING
        session.status = 'TRAINING'
        session.save()

        try:
            # Train the model
            disease = session.disease
            training_start = session.training_start_date.strftime('%Y-%m-%d')
            training_end = session.training_end_date.strftime('%Y-%m-%d')
            forecast_start = session.forecast_start_date.strftime('%Y-%m-%d')
            forecast_end = session.forecast_end_date.strftime('%Y-%m-%d')

            self.stdout.write('Training model...')
            
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

            self.stdout.write(self.style.SUCCESS(f'Model trained! MAE: {metrics["train_mae"]:.4f}'))

            # Save model to registry
            model_name = f'{disease.lower()}_model_custom_{session.id}'
            model_path = save_model(model, model_name)
            self.stdout.write(f'Model saved to: {model_path}')

            # Create ForecastModel record
            forecast_model = ForecastModel.objects.create(
                name=model_name,
                version=f'custom_{session.id}',
                algorithm='RandomForest',
                disease=disease,
                description=f'Custom training: {training_start} to {training_end}',
                model_file=model_path,
                trained_by=session.trained_by,
                trained_at=timezone.now(),
                status='TRAINED',
                accuracy=metrics.get('train_mae'),
                metrics=metrics
            )

            # Link to session
            session.model = forecast_model
            session.mae_score = metrics['train_mae']
            session.trained_at = timezone.now()

            # Generate forecasts
            self.stdout.write('Generating forecasts...')
            
            if disease == 'MALARIA':
                forecasts_data = generate_malaria_forecast(
                    model, feature_cols, forecast_start, forecast_end
                )
            else:
                forecasts_data = generate_dengue_forecast(
                    model, feature_cols, forecast_start, forecast_end
                )

            # Save forecasts to database
            forecast_count = 0
            for forecast_dict in forecasts_data:
                Forecast.objects.create(
                    model=forecast_model,
                    training_session=session,
                    disease=disease,
                    region='Pakistan',
                    forecast_date=forecast_dict['date'],
                    predicted_cases=forecast_dict['predicted_cases'],
                    actual_cases=forecast_dict.get('actual_cases'),
                    confidence_interval=forecast_dict.get('confidence_interval', {}),
                    metadata=forecast_dict.get('metadata', {}),
                    created_by=session.trained_by
                )
                forecast_count += 1

            self.stdout.write(self.style.SUCCESS(f'Generated {forecast_count} forecasts'))

            # Update session status
            session.status = 'COMPLETED'
            session.metadata = {
                'forecast_count': forecast_count,
                'model_path': model_path,
                'metrics': metrics
            }
            session.save()

            self.stdout.write(self.style.SUCCESS(
                f'Training session {session_id} completed successfully!'
            ))

        except Exception as e:
            # Update session status to FAILED
            session.status = 'FAILED'
            session.metadata = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            session.save()

            self.stdout.write(self.style.ERROR(f'Training failed: {str(e)}'))
            self.stdout.write(traceback.format_exc())
