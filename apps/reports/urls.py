"""
Reports App URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

app_name = 'reports'

urlpatterns = [
    path('', include(router.urls)),
]
