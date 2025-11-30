"""
Forecasting App - ML model training and predictions

This app provides:
- ML model training (using scikit-learn)
- Disease outbreak forecasting
- Model versioning and registry
- Async training with Celery

For learning:
- Models are trained on uploaded datasets
- Trained models saved to storage/model_registry/
- Predictions cached for performance
"""

from django.db import models
from django.conf import settings


class ForecastModel(models.Model):
    """
    ML Model Registry
    
    Tracks trained models, their versions, and performance metrics.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('TRAINING', 'Training'),
        ('TRAINED', 'Trained'),
        ('FAILED', 'Failed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    algorithm = models.CharField(max_length=100)  # e.g., "RandomForest", "ARIMA"
    disease = models.CharField(max_length=100, default='UNKNOWN')  # MALARIA, DENGUE, etc.
    description = models.TextField(blank=True, null=True)
    
    # Model file path
    model_file = models.CharField(max_length=500, blank=True, null=True)
    
    # Training metadata
    trained_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trained_models'
    )
    
    trained_at = models.DateTimeField(null=True, blank=True)
    
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='models'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True)
    metrics = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.status})"


class TrainingSession(models.Model):
    """
    Training Session Configuration
    
    Tracks custom training/forecasting configurations for model retraining.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('TRAINING', 'Training'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    disease = models.CharField(max_length=100)  # MALARIA, DENGUE
    
    # Training date range
    training_start_date = models.DateField()
    training_end_date = models.DateField()
    
    # Forecast date range
    forecast_start_date = models.DateField()
    forecast_end_date = models.DateField()
    
    # Training results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    mae_score = models.FloatField(null=True, blank=True)
    
    # Associated model
    model = models.ForeignKey(
        ForecastModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_sessions'
    )
    
    # Metadata
    metadata = models.JSONField(null=True, blank=True)
    
    trained_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_sessions'
    )
    
    trained_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.disease} Training ({self.training_start_date} to {self.training_end_date})"


class Forecast(models.Model):
    """
    Forecast Results
    
    Stores predictions made by trained models.
    """
    
    model = models.ForeignKey(
        ForecastModel,
        on_delete=models.CASCADE,
        related_name='forecasts'
    )
    
    # Link to training session if created from custom training
    training_session = models.ForeignKey(
        TrainingSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forecasts'
    )
    
    # Forecast data
    disease = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    forecast_date = models.DateField()
    predicted_cases = models.IntegerField(null=True, blank=True)
    actual_cases = models.IntegerField(null=True, blank=True)
    confidence_interval = models.JSONField(null=True, blank=True)
    
    # Additional metadata from prediction
    metadata = models.JSONField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forecasts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-forecast_date']
        indexes = [
            models.Index(fields=['disease', 'forecast_date']),
            models.Index(fields=['disease', 'region', 'forecast_date']),
        ]
    
    def __str__(self):
        return f"{self.disease} - {self.region} ({self.forecast_date})"
