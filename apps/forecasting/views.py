"""
Forecasting Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Min, Max
from datetime import datetime, timedelta
from .models import ForecastModel, Forecast, TrainingSession
from .serializers import ForecastModelSerializer, ForecastSerializer
from .tasks import train_custom_model
from apps.datasets.models import LabTest, PharmacySales


class ForecastModelViewSet(viewsets.ModelViewSet):
    """
    Forecast Model API Endpoints
    
    GET /api/forecasting/models/ - List all models
    POST /api/forecasting/models/ - Create and train new model
    GET /api/forecasting/models/{id}/ - Get model details
    """
    
    queryset = ForecastModel.objects.all()
    serializer_class = ForecastModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['disease', 'status']
    ordering_fields = ['created_at', 'trained_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Save model and trigger training"""
        model = serializer.save(trained_by=self.request.user)
        
        # Trigger async training task
        train_model.delay(model.id)
    
    @action(detail=True, methods=['post'])
    def retrain(self, request, pk=None):
        """Trigger model retraining"""
        model = self.get_object()
        train_model.delay(model.id)
        return Response({'status': 'Training queued'})


class DataRangeView(viewsets.ViewSet):
    """
    Data Range API - Returns available date ranges for training
    
    GET /api/forecasting/data-range/?disease=MALARIA
    
    Returns:
    {
        "disease": "MALARIA",
        "lab_test_start": "2023-01-01",
        "lab_test_end": "2024-09-30",
        "pharma_start": "2023-01-15",
        "pharma_end": "2024-09-25",
        "training_start": "2023-01-15",  # max of lab/pharma starts
        "training_end": "2024-09-25"      # min of lab/pharma ends
    }
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        disease = request.query_params.get('disease', 'MALARIA')
        
        # Get lab test date range
        lab_range = LabTest.objects.filter(disease=disease).aggregate(
            start=Min('date'),
            end=Max('date')
        )
        
        # Get pharmacy sales date range
        # Determine which medicines to query based on disease
        if disease == 'MALARIA':
            medicine_filter = {'medicine__in': ['Coartem', 'Fansidar']}
        elif disease == 'DENGUE':
            medicine_filter = {'medicine__in': ['Panadol', 'Calpol']}
        else:
            medicine_filter = {}
        
        pharma_range = PharmacySales.objects.filter(**medicine_filter).aggregate(
            start=Min('date'),
            end=Max('date')
        )
        
        # Calculate valid training range
        training_start = max(lab_range['start'], pharma_range['start']) if lab_range['start'] and pharma_range['start'] else None
        training_end = min(lab_range['end'], pharma_range['end']) if lab_range['end'] and pharma_range['end'] else None
        
        return Response({
            'disease': disease,
            'lab_test_start': lab_range['start'],
            'lab_test_end': lab_range['end'],
            'pharma_start': pharma_range['start'],
            'pharma_end': pharma_range['end'],
            'training_start': training_start,
            'training_end': training_end,
        })


class TrainingSessionViewSet(viewsets.ViewSet):
    """
    Training Session API - Configure and trigger custom model training
    
    POST /api/forecasting/training-sessions/
    Body:
    {
        "disease": "MALARIA",
        "training_start_date": "2023-01-01",
        "training_end_date": "2024-09-30",
        "forecast_start_date": "2024-10-01",
        "forecast_end_date": "2024-12-31"
    }
    
    GET /api/forecasting/training-sessions/
    Returns list of all training sessions
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        print(f"==== TRAINING SESSION CREATE REQUEST ====")
        print(f"Request data: {request.data}")
        
        data = request.data
        
        disease = data.get('disease')
        training_start = datetime.strptime(data.get('training_start_date'), '%Y-%m-%d').date()
        training_end = datetime.strptime(data.get('training_end_date'), '%Y-%m-%d').date()
        forecast_start = datetime.strptime(data.get('forecast_start_date'), '%Y-%m-%d').date()
        forecast_end = datetime.strptime(data.get('forecast_end_date'), '%Y-%m-%d').date()
        
        print(f"Parsed dates: disease={disease}, train={training_start} to {training_end}, forecast={forecast_start} to {forecast_end}")
        
        # Validation 1: Training dates must be sequential
        if training_start >= training_end:
            return Response(
                {'error': 'Training start date must be before training end date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation 2: Forecast dates must be sequential
        if forecast_start >= forecast_end:
            return Response(
                {'error': 'Forecast start date must be before forecast end date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation 3: Forecast must start immediately after training ends
        expected_forecast_start = training_end + timedelta(days=1)
        if forecast_start != expected_forecast_start:
            return Response(
                {
                    'error': 'Forecast start date must be immediately after training end date',
                    'expected': expected_forecast_start.strftime('%Y-%m-%d'),
                    'received': forecast_start.strftime('%Y-%m-%d')
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create training session
        session = TrainingSession.objects.create(
            disease=disease,
            training_start_date=training_start,
            training_end_date=training_end,
            forecast_start_date=forecast_start,
            forecast_end_date=forecast_end,
            trained_by=request.user,
            status='PENDING'
        )
        
        print(f"Training session created: id={session.id}, status={session.status}")
        
        # Trigger async training task with Celery
        print(f"Triggering train_custom_model.delay({session.id})")
        task = train_custom_model.delay(session.id)
        print(f"Task triggered: task_id={task.id}")
        
        return Response({
            'id': session.id,
            'status': 'Training started in background',
            'task_id': task.id,
            'disease': disease,
            'training_range': f"{training_start} to {training_end}",
            'forecast_range': f"{forecast_start} to {forecast_end}",
            'note': 'Training is running in background. Refresh training history to see progress.'
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request):
        """List all training sessions"""
        sessions = TrainingSession.objects.all().values(
            'id', 'disease', 'training_start_date', 'training_end_date',
            'forecast_start_date', 'forecast_end_date', 'status', 'mae_score',
            'trained_at', 'created_at'
        )
        return Response(list(sessions))


class ForecastViewSet(viewsets.ModelViewSet):
    """
    Forecast API Endpoints
    
    GET /api/forecasting/forecasts/ - List all forecasts
    GET /api/forecasting/forecasts/?disease=MALARIA - Filter by disease
    GET /api/forecasting/forecasts/?forecast_date__gte=2024-10-01 - Filter by date
    POST /api/forecasting/forecasts/ - Generate new forecast
    GET /api/forecasting/forecasts/{id}/ - Get forecast details
    GET /api/forecasting/forecasts/available_dates/ - Get all available forecast dates
    GET /api/forecasting/forecasts/forecast_detail/ - Get forecasts for specific date range
    """
    
    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['disease', 'region', 'forecast_date']
    ordering_fields = ['forecast_date', 'created_at']
    ordering = ['-forecast_date']
    
    def list(self, request, *args, **kwargs):
        """Override list to add debug logging"""
        disease_filter = request.query_params.get('disease')
        
        # Log what's being requested
        print(f"Forecast list requested - disease filter: {disease_filter}")
        print(f"Total forecasts in DB: {Forecast.objects.count()}")
        
        # Also check what training data we have
        from apps.datasets.models import LabTest, PharmacySales
        lab_count = LabTest.objects.count()
        pharmacy_count = PharmacySales.objects.count()
        print(f"Training data available: LabTest={lab_count}, PharmacySales={pharmacy_count}")
        
        if disease_filter:
            count = Forecast.objects.filter(disease=disease_filter).count()
            print(f"Forecasts for {disease_filter}: {count}")
            
            # Show sample forecasts
            sample = Forecast.objects.filter(disease=disease_filter)[:5].values(
                'id', 'disease', 'forecast_date', 'predicted_cases', 'created_at'
            )
            print(f"Sample forecasts: {list(sample)}")
        
        return super().list(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Save forecast and trigger generation"""
        forecast = serializer.save(created_by=self.request.user)
        
        # Trigger async forecast generation
        generate_forecast.delay(forecast.id)
    
    @action(detail=False, methods=['get'])
    def available_dates(self, request):
        """
        Get all available forecast dates grouped by disease
        
        GET /api/forecasting/forecasts/available_dates/?disease=MALARIA
        
        Returns:
        {
            "disease": "MALARIA",
            "available_dates": [
                {
                    "date": "2024-10-01",
                    "has_actual": true,
                    "predicted_cases": 15,
                    "actual_cases": 18
                },
                ...
            ],
            "date_range": {
                "start": "2024-10-01",
                "end": "2024-12-31"
            },
            "total_forecasts": 92
        }
        """
        disease = request.query_params.get('disease', 'MALARIA')
        
        forecasts = Forecast.objects.filter(disease=disease).order_by('forecast_date').values(
            'forecast_date', 'predicted_cases', 'actual_cases'
        )
        
        available_dates = [
            {
                'date': f['forecast_date'],
                'has_actual': f['actual_cases'] is not None,
                'predicted_cases': f['predicted_cases'],
                'actual_cases': f['actual_cases']
            }
            for f in forecasts
        ]
        
        date_range = Forecast.objects.filter(disease=disease).aggregate(
            start=Min('forecast_date'),
            end=Max('forecast_date')
        )
        
        return Response({
            'disease': disease,
            'available_dates': available_dates,
            'date_range': date_range,
            'total_forecasts': len(available_dates)
        })

    @action(detail=False, methods=['get'])
    def forecast_detail(self, request):
        """
        Get detailed forecasts for a specific date range

        GET /api/forecasting/forecasts/forecast_detail/?disease=MALARIA&start_date=2024-10-01&days_ahead=30        Returns:
        {
            "disease": "MALARIA",
            "start_date": "2024-10-01",
            "days_ahead": 30,
            "forecasts": [
                {
                    "date": "2024-10-01",
                    "predicted_cases": 15,
                    "actual_cases": 18,
                    "accuracy": 83.33,
                    "lower_bound": 5,
                    "upper_bound": 25,
                    "has_actual": true
                },
                ...
            ],
            "summary": {
                "total_days": 30,
                "days_with_actual": 15,
                "average_accuracy": 85.5,
                "average_mae": 2.5
            }
        }
        """
        disease = request.query_params.get('disease', 'MALARIA')
        start_date_str = request.query_params.get('start_date')
        days_ahead = int(request.query_params.get('days_ahead', 30))
        
        if not start_date_str:
            return Response(
                {'error': 'start_date parameter is required (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        end_date = start_date + timedelta(days=days_ahead - 1)
        
        # Check if forecasts exist for this range
        forecasts_qs = Forecast.objects.filter(
            disease=disease,
            forecast_date__gte=start_date,
            forecast_date__lte=end_date
        ).order_by('forecast_date')
        
        if not forecasts_qs.exists():
            return Response(
                {
                    'error': 'No forecasts available for this date range',
                    'disease': disease,
                    'requested_range': f"{start_date} to {end_date}",
                    'available_range': Forecast.objects.filter(disease=disease).aggregate(
                        start=Min('forecast_date'),
                        end=Max('forecast_date')
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build detailed forecast list
        forecasts_list = []
        total_accuracy = 0
        total_mae = 0
        days_with_actual = 0
        
        for f in forecasts_qs:
            has_actual = f.actual_cases is not None
            accuracy = None
            mae = None
            
            if has_actual and f.actual_cases > 0:
                accuracy = max(0, 100 - abs(f.predicted_cases - f.actual_cases) / f.actual_cases * 100)
                mae = abs(f.predicted_cases - f.actual_cases)
                total_accuracy += accuracy
                total_mae += mae
                days_with_actual += 1
            
            # Extract confidence interval bounds
            ci = f.confidence_interval or {}
            lower = ci.get('lower', 0)
            upper = ci.get('upper', f.predicted_cases * 2)
            
            forecasts_list.append({
                'date': f.forecast_date,
                'predicted_cases': f.predicted_cases,
                'actual_cases': f.actual_cases,
                'accuracy': round(accuracy, 2) if accuracy else None,
                'mae': mae,
                'lower_bound': lower,
                'upper_bound': upper,
                'has_actual': has_actual
            })
        
        # Calculate summary statistics
        avg_accuracy = round(total_accuracy / days_with_actual, 2) if days_with_actual > 0 else None
        avg_mae = round(total_mae / days_with_actual, 2) if days_with_actual > 0 else None
        
        return Response({
            'disease': disease,
            'start_date': start_date,
            'end_date': end_date,
            'days_ahead': days_ahead,
            'forecasts': forecasts_list,
            'summary': {
                'total_days': len(forecasts_list),
                'days_with_actual': days_with_actual,
                'average_accuracy': avg_accuracy,
                'average_mae': avg_mae
            }
        })

