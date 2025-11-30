"""
Reports App - Generate and export reports

This app provides:
- Report generation (PDF, Excel, CSV)
- Analytics and aggregations
- Audit logging
- Export functionality

For learning:
- Reports can be generated async for large datasets
- Multiple export formats supported
- Audit trail for compliance
"""

from django.db import models
from django.conf import settings


class Report(models.Model):
    """
    Report Model
    
    Stores generated reports and their metadata.
    """
    
    TYPE_CHOICES = [
        ('FORECAST', 'Forecast Report'),
        ('ANALYTICS', 'Analytics Report'),
        ('AUDIT', 'Audit Log Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    
    # Report configuration
    parameters = models.JSONField(null=True, blank=True)
    
    # Generated file
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"


class AuditLog(models.Model):
    """
    Audit Log Model
    
    Tracks all important actions for compliance and debugging.
    """
    
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('UPLOAD', 'Dataset Upload'),
        ('TRAIN', 'Model Training'),
        ('FORECAST', 'Forecast Generated'),
        ('EXPORT', 'Report Exported'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.action} ({self.created_at})"
