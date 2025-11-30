"""
Forecasting App URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForecastModelViewSet, ForecastViewSet, DataRangeView, TrainingSessionViewSet

router = DefaultRouter()
router.register(r'models', ForecastModelViewSet, basename='forecast-model')
router.register(r'forecasts', ForecastViewSet, basename='forecast')
router.register(r'data-range', DataRangeView, basename='data-range')
router.register(r'training-sessions', TrainingSessionViewSet, basename='training-session')

app_name = 'forecasting'

urlpatterns = [
    path('', include(router.urls)),
]
