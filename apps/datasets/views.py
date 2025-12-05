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

        # Run validation SYNCHRONOUSLY (not via Celery)
        # This ensures immediate feedback and no stuck "Validating" status
        try:
            print(f"==== STARTING DATASET VALIDATION FOR DATASET {dataset.id} ====")
            print(f"Dataset: {dataset.name}")
            metadata = dataset.validation_errors or {}
            print(f"Type: {metadata.get('dataset_type', 'UNKNOWN')}, Disease: {metadata.get('disease', 'UNKNOWN')}")
            
            # Import the actual validation function (not the Celery task)
            from .tasks import validate_dataset as validate_dataset_task
            
            # Call it directly - this is synchronous
            result = validate_dataset_task(dataset.id)
            
            print(f"==== VALIDATION COMPLETED ====")
            print(f"Result: {result}")
            
            # Refresh dataset from database to get updated status
            dataset.refresh_from_db()
            print(f"Final dataset status: {dataset.status}")
            
            if dataset.status == 'INVALID':
                print(f"Validation errors: {dataset.validation_errors}")
            elif dataset.status == 'PROCESSED':
                print(f"Successfully imported {dataset.row_count} rows, {dataset.column_count} columns")
                
        except Exception as e:
            # Log the full error
            print(f"==== VALIDATION TASK FAILED ====")
            print(f"Error: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Update dataset status to show error
            dataset.status = 'INVALID'
            dataset.validation_errors = {
                'errors': [f'Validation task failed: {str(e)}']
            }
            dataset.save()
            raise
    
    @action(detail=True, methods=['post'])
    def revalidate(self, request, pk=None):
        """Manually trigger revalidation of a dataset"""
        dataset = self.get_object()
        validate_dataset.delay(dataset.id)
        return Response({'status': 'Validation queued'})
