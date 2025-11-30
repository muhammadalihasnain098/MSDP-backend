"""
Forecasting Serializers
"""

from rest_framework import serializers
from .models import ForecastModel, Forecast


class ForecastModelSerializer(serializers.ModelSerializer):
    """Serializer for ForecastModel"""
    
    trained_by_name = serializers.CharField(
        source='trained_by.username',
        read_only=True
    )
    
    class Meta:
        model = ForecastModel
        fields = ['id', 'name', 'version', 'algorithm', 'status',
                  'trained_by', 'trained_by_name', 'dataset',
                  'accuracy', 'metrics', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'accuracy', 'metrics',
                            'created_at', 'updated_at']


class ForecastSerializer(serializers.ModelSerializer):
    """Serializer for Forecast"""
    
    model_name = serializers.CharField(
        source='model.name',
        read_only=True
    )
    
    class Meta:
        model = Forecast
        fields = ['id', 'model', 'model_name', 'disease', 'region',
                  'forecast_date', 'predicted_cases', 'confidence_interval',
                  'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']
