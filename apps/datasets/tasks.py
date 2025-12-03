"""
Dataset Celery Tasks

Background tasks for dataset processing.

For learning:
- @shared_task decorator makes tasks discoverable by Celery
- Tasks run in background workers (not blocking the API)
- Can process large files without timeout
"""

from celery import shared_task
from datetime import datetime


@shared_task
def validate_dataset(dataset_id):
    """
    Validate and import uploaded dataset
    
    This task:
    1. Reads the uploaded file
    2. Checks for required columns
    3. Validates data types
    4. Imports data into LabTest or PharmacySales
    5. Updates dataset status
    """
    # Import here to avoid issues with Django app loading
    import pandas as pd
    from .models import Dataset, LabTest, PharmacySales


@shared_task
def validate_dataset(dataset_id):
    """
    Validate and import uploaded dataset
    
    This task:
    1. Reads the uploaded file
    2. Checks for required columns
    3. Validates data types
    4. Imports data into LabTest or PharmacySales
    5. Updates dataset status
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = 'VALIDATING'
        dataset.save()
        
        # Get metadata
        metadata = dataset.validation_errors or {}
        dataset_type = metadata.get('dataset_type', 'LAB')
        disease = metadata.get('disease', 'MALARIA')
        
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
            dataset.status = 'INVALID'
            dataset.validation_errors = {'errors': errors}
            dataset.save()
            return {'status': 'error', 'errors': errors}
        
        # Validate and import based on dataset type
        if dataset_type == 'LAB':
            errors = _import_lab_data(df, disease)
        elif dataset_type == 'PHARMACY':
            errors = _import_pharmacy_data(df)
        else:
            errors.append(f"Unknown dataset type: {dataset_type}")
        
        # Store metadata
        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        
        # Update status based on validation
        if errors:
            dataset.status = 'INVALID'
            dataset.validation_errors = {'errors': errors}
        else:
            dataset.status = 'PROCESSED'
            dataset.validation_errors = None
        
        dataset.save()
        
        return {'status': 'success', 'dataset_id': dataset_id, 'rows_imported': len(df)}
    
    except Exception as e:
        # Handle errors
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = 'INVALID'
        dataset.validation_errors = {'errors': [str(e)]}
        dataset.save()
        
        return {'status': 'error', 'message': str(e)}


def _import_lab_data(df, disease):
    """Import lab test data from DataFrame"""
    from .models import LabTest
    errors = []
    
    # Check required columns
    required_columns = ['date', 'positive_tests', 'total_tests']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        return errors
    
    # Import data
    imported_count = 0
    for _, row in df.iterrows():
        try:
            # Parse date (handle both DD/MM/YYYY and YYYY-MM-DD)
            date_str = str(row['date'])
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
            
            # Create or update LabTest record
            LabTest.objects.update_or_create(
                date=date_obj,
                disease=disease,
                defaults={
                    'positive_tests': int(row['positive_tests']),
                }
            )
            imported_count += 1
        except Exception as e:
            errors.append(f"Row error: {str(e)}")
    
    if imported_count > 0:
        print(f"Imported {imported_count} lab test records for {disease}")
    
    return errors


def _import_pharmacy_data(df):
    """Import pharmacy sales data from DataFrame"""
    from .models import PharmacySales
    errors = []
    
    # Check required columns
    required_columns = ['date', 'brand_name', 'total_sales']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        return errors
    
    # Import data
    imported_count = 0
    for _, row in df.iterrows():
        try:
            # Parse date
            date_str = str(row['date'])
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
            
            # Create or update PharmacySales record
            PharmacySales.objects.update_or_create(
                date=date_obj,
                medicine=str(row['brand_name']),
                defaults={
                    'sale': float(row['total_sales']),
                }
            )
            imported_count += 1
        except Exception as e:
            errors.append(f"Row error: {str(e)}")
    
    if imported_count > 0:
        print(f"Imported {imported_count} pharmacy sales records")
    
    return errors
