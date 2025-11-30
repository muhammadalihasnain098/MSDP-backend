"""
URL Configuration for MSDP Backend

This file routes incoming requests to the appropriate app.
Each app has its own urls.py file for better organization.

For learning:
- 'api/users/' routes to the users app (authentication, profiles)
- 'api/datasets/' routes to the datasets app (file uploads, validation)
- 'api/forecasting/' routes to the forecasting app (ML predictions)
- 'api/reports/' routes to the reports app (export, analytics)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints (version 1)
    path('api/users/', include('apps.users.urls')),
    path('api/datasets/', include('apps.datasets.urls')),
    path('api/forecasting/', include('apps.forecasting.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
