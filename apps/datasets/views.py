"""
Dataset Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Dataset
from .serializers import DatasetSerializer, DatasetUploadSerializer
from .tasks import validate_dataset


class DatasetViewSet(viewsets.ModelViewSet):
    """
    Dataset API Endpoints
    
    GET /api/datasets/ - List all datasets
    POST /api/datasets/ - Upload new dataset
    GET /api/datasets/{id}/ - Get dataset details
    DELETE /api/datasets/{id}/ - Delete dataset
    """
    
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializer for upload"""
        if self.action == 'create':
            return DatasetUploadSerializer
        return DatasetSerializer
    
    def perform_create(self, serializer):
        """Save dataset and trigger validation task"""
        dataset = serializer.save(uploaded_by=self.request.user)
        
        # Trigger async validation task
        validate_dataset.delay(dataset.id)
    
    @action(detail=True, methods=['post'])
    def revalidate(self, request, pk=None):
        """Manually trigger revalidation of a dataset"""
        dataset = self.get_object()
        validate_dataset.delay(dataset.id)
        return Response({'status': 'Validation queued'})
