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


# Disease-Medicine Mapping
DISEASE_MEDICINE_MAP = {
    'DENGUE': [
        'Panadol', 'Calpol', 'Febrol', 'Disprol', 'Relifal', 'Plasaline', 
        'Medisol', 'Medilact-D', 'Hartmann\'s Solution', 'Lensaline', 
        'Dextrone-40', 'ORS (Oral Rehydration Salts)', 'Vitamin C Tablets', 
        'Folic Acid Tablets', 'Platelet Transfusion', 'Paracetamol (Panadol, Calpol, Febrol)'
    ],
    'ANTIMALARIA': [
        'Bassoquin', 'Amdaquin', 'Amoquine', 'Unesoquine', 'Fansidar', 
        'Geridar', 'Neosidar', 'Sulfadar', 'Fantar DS', 'One-3 Syrup', 
        'Artheget', 'Gen-M', 'Mosquinet', 'Coartem'
    ],
    'CHOLERA': [
        'Biolyte ORS Sachet', 'Rediplex ORS Sachet', 'Paedi Care ORS (Lemon)',
        'Paedi Care ORS (Strawberry)', 'Werisol ORS Powder', 'Rehydro ORS (Orange)',
        'BL BioLyte ORS (Lemon)', 'ORS (GSK)', 'Chloramphenicol (Irza)',
        'Doxycycline (Cherdox)', 'Tetracycline HCl', 'Azithromycin (Zithrocin)',
        'Ciprofloxacin (Ciproxin)', 'Zincat', 'ORS Liquid (Care ORS)'
    ],
    'DIARRHOEA': [
        'Pedialyte,', 'ORS-L,', 'Hydro,', 'Zincolak,', 'Zincat,', 
        'Enterogermina,', 'Lacteol Fort,', 'Vomil-S,', 'Hidrasec,', 
        'Rotarix,', 'RotaTeq,', 'Calpol,', 'Panadol,', 'Flagyl,', 'Bifilac'
    ]
}


def _detect_disease_from_medicine(medicine_name):
    """
    Detect which disease(s) a medicine treats by matching against the mapping.
    Returns a list of diseases.
    """
    medicine_name_lower = medicine_name.lower().strip()
    detected_diseases = []
    
    for disease, medicines in DISEASE_MEDICINE_MAP.items():
        for med in medicines:
            # Check if medicine name contains the mapped medicine or vice versa
            if (medicine_name_lower in med.lower() or 
                med.lower() in medicine_name_lower or
                medicine_name_lower == med.lower()):
                detected_diseases.append(disease)
                break
    
    return detected_diseases if detected_diseases else ['UNKNOWN']


def _analyze_pharmacy_file_disease(df, medicine_col):
    """
    Analyze entire pharmacy file to determine which disease it belongs to.
    Uses threshold approach: if 2+ medicines match a disease category, file is for that disease.
    Returns the primary disease or UNKNOWN.
    """
    disease_match_count = {}
    
    for _, row in df.iterrows():
        medicine_name = str(row[medicine_col]).strip()
        diseases = _detect_disease_from_medicine(medicine_name)
        
        for disease in diseases:
            if disease != 'UNKNOWN':
                disease_match_count[disease] = disease_match_count.get(disease, 0) + 1
    
    # Find disease with most matches
    if disease_match_count:
        # Get disease with highest count
        primary_disease = max(disease_match_count, key=disease_match_count.get)
        match_count = disease_match_count[primary_disease]
        
        # Threshold: at least 2 medicines must match
        if match_count >= 2:
            print(f"File classified as {primary_disease} disease (matched {match_count} medicines)")
            print(f"All disease matches: {disease_match_count}")
            return primary_disease
    
    print(f"File could not be classified - disease matches: {disease_match_count}")
    return 'UNKNOWN'


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
        # Handle errors - reimport in case of error
        from .models import Dataset
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = 'INVALID'
        dataset.validation_errors = {'errors': [str(e)]}
        dataset.save()
        
        return {'status': 'error', 'message': str(e)}


def _import_lab_data(df, disease):
    """Import lab test data from DataFrame"""
    from .models import LabTest
    errors = []
    
    # Check required columns - accept either 'positive_tests' or 'cases'
    required_columns = ['date', 'total_tests']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    # Check for positive tests column (accept either name)
    has_positive_tests = 'positive_tests' in df.columns
    has_cases = 'cases' in df.columns
    
    if not (has_positive_tests or has_cases):
        missing_columns.append('positive_tests or cases')
    
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}")
        return errors
    
    # Determine which column to use for positive tests
    positive_col = 'positive_tests' if has_positive_tests else 'cases'
    
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
                    'positive_tests': int(row[positive_col]),
                }
            )
            imported_count += 1
        except Exception as e:
            errors.append(f"Row error: {str(e)}")
    
    if imported_count > 0:
        print(f"Imported {imported_count} lab test records for {disease}")
    
    return errors


def _import_pharmacy_data(df):
    """
    Import pharmacy sales data from DataFrame with automatic disease detection.
    Analyzes the entire file to determine which disease it belongs to (threshold: 2+ medicine matches).
    """
    from .models import PharmacySales
    errors = []
    
    # Check required columns - accept various column name variations
    date_col = None
    medicine_col = None
    sales_col = None
    
    # Find date column
    for col in df.columns:
        if col.lower() in ['date', 'day', 'tanggal']:
            date_col = col
            break
    
    # Find medicine/brand column
    for col in df.columns:
        if col.lower() in ['brand_name', 'brand / product name', 'medicine', 'product', 'drug', 'obat', 'brand/name']:
            medicine_col = col
            break
    
    # Find sales column
    for col in df.columns:
        if col.lower() in ['total_sales', 'sales', 'sale', 'amount', 'quantity', 'jumlah']:
            sales_col = col
            break
    
    missing = []
    if not date_col:
        missing.append('date')
    if not medicine_col:
        missing.append('brand_name or medicine')
    if not sales_col:
        missing.append('total_sales or sales')
    
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}. Found columns: {', '.join(df.columns)}")
        return errors
    
    # Analyze entire file to determine primary disease category
    file_disease = _analyze_pharmacy_file_disease(df, medicine_col)
    
    if file_disease == 'UNKNOWN':
        errors.append("Warning: Could not classify file into any disease category (threshold: 2+ matching medicines required)")
    
    # Import data
    imported_count = 0
    
    for _, row in df.iterrows():
        try:
            # Parse date
            date_str = str(row[date_col])
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
                    except ValueError:
                        # Try parsing as just date number
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
            
            medicine_name = str(row[medicine_col]).strip()
            sales_value = float(row[sales_col])
            
            # Detect individual medicine's disease category
            medicine_diseases = _detect_disease_from_medicine(medicine_name)
            medicine_disease = medicine_diseases[0] if medicine_diseases else 'UNKNOWN'
            
            # Create or update PharmacySales record
            PharmacySales.objects.update_or_create(
                date=date_obj,
                medicine=medicine_name,
                defaults={
                    'sale': sales_value,
                    'disease_category': medicine_disease,
                }
            )
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row error at {row.get(date_col, 'unknown date')}: {str(e)}")
    
    if imported_count > 0:
        print(f"Imported {imported_count} pharmacy sales records for {file_disease} disease")
    
    return errors
