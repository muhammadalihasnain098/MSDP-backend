from django.contrib import admin
from .models import ForecastModel, Forecast


@admin.register(ForecastModel)
class ForecastModelAdmin(admin.ModelAdmin):
    """Admin interface for ForecastModel"""
    
    list_display = ['name', 'version', 'algorithm', 'status', 'accuracy', 'created_at']
    list_filter = ['status', 'algorithm', 'created_at']
    search_fields = ['name', 'version']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    """Admin interface for Forecast"""
    
    list_display = ['disease', 'region', 'forecast_date', 'predicted_cases', 'created_at']
    list_filter = ['disease', 'region', 'forecast_date']
    search_fields = ['disease', 'region']
    readonly_fields = ['created_at']
