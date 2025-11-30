"""
Reports Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import FileResponse
from .models import Report, AuditLog
from .serializers import ReportSerializer, AuditLogSerializer
from .tasks import generate_report


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report API Endpoints
    
    GET /api/reports/ - List all reports
    POST /api/reports/ - Create new report
    GET /api/reports/{id}/ - Get report details
    GET /api/reports/{id}/download/ - Download report file
    """
    
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Save report and trigger generation"""
        report = serializer.save(generated_by=self.request.user)
        
        # Trigger async report generation
        generate_report.delay(report.id)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download generated report file"""
        report = self.get_object()
        
        if report.status != 'COMPLETED':
            return Response(
                {'error': 'Report not ready yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not report.file:
            return Response(
                {'error': 'Report file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            report.file.open('rb'),
            as_attachment=True,
            filename=report.file.name
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit Log API Endpoints (Admin only)
    
    GET /api/reports/audit-logs/ - List all audit logs
    GET /api/reports/audit-logs/{id}/ - Get audit log details
    """
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
