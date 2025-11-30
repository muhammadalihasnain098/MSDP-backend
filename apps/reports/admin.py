from django.contrib import admin
from .models import Report, AuditLog


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin interface for Report"""
    
    list_display = ['title', 'report_type', 'format', 'status', 'generated_by', 'created_at']
    list_filter = ['report_type', 'format', 'status', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog"""
    
    list_display = ['user', 'action', 'description', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']
