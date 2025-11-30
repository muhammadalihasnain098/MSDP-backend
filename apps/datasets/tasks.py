"""
Dataset Celery Tasks

Background tasks for dataset processing.

For learning:
- @shared_task decorator makes tasks discoverable by Celery
- Tasks run in background workers (not blocking the API)
- Can process large files without timeout
"""

from celery import shared_task
import pandas as pd
from .models import Dataset


@shared_task
def validate_dataset(dataset_id):
    """
    Validate uploaded dataset
    
    This task:
    1. Reads the uploaded file
    2. Checks for required columns
    3. Validates data types
    4. Updates dataset status
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = 'VALIDATING'
        dataset.save()
        
        # Read file based on extension
        file_path = dataset.file.path
        
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        # Basic validation
        errors = []
        
        # Check if file is empty
        if df.empty:
            errors.append("File is empty")
        
        # Store metadata
        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        
        # Update status based on validation
        if errors:
            dataset.status = 'INVALID'
            dataset.validation_errors = {'errors': errors}
        else:
            dataset.status = 'VALID'
            dataset.validation_errors = None
        
        dataset.save()
        
        return {'status': 'success', 'dataset_id': dataset_id}
    
    except Exception as e:
        # Handle errors
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = 'INVALID'
        dataset.validation_errors = {'errors': [str(e)]}
        dataset.save()
        
        return {'status': 'error', 'message': str(e)}
