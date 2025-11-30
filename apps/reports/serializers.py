"""
Reports Serializers
"""

from rest_framework import serializers
from .models import Report, AuditLog


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report"""
    
    generated_by_name = serializers.CharField(
        source='generated_by.username',
        read_only=True
    )
    
    class Meta:
        model = Report
        fields = ['id', 'title', 'report_type', 'format', 'parameters',
                  'file', 'status', 'generated_by', 'generated_by_name',
                  'created_at', 'completed_at']
        read_only_fields = ['id', 'file', 'status', 'completed_at',
                            'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog"""
    
    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'action', 'description',
                  'ip_address', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']
