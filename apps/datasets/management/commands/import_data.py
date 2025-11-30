"""
Management Command: import_data

Imports all CSV data from the MODELS folder into Django database.
This preserves the exact data structure used in the Jupyter notebooks.

Usage:
    python manage.py import_data
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.datasets.models import LabTest, PharmacySales


class Command(BaseCommand):
    help = 'Import lab test and pharmacy sales data from CSV files'

    def handle(self, *args, **options):
        # Path to MODELS folder
        models_dir = os.path.join(settings.BASE_DIR, 'MODELS')
        
        if not os.path.exists(models_dir):
            self.stdout.write(self.style.ERROR(f'MODELS directory not found: {models_dir}'))
            return
        
        self.stdout.write(self.style.SUCCESS('Starting data import...'))
        
        # Import Malaria Lab Test Data
        self.import_malaria_lab_tests(models_dir)
        
        # Import Dengue Lab Test Data
        self.import_dengue_lab_tests(models_dir)
        
        # Import Pharmacy Sales Data
        self.import_pharmacy_sales(models_dir)
        
        self.stdout.write(self.style.SUCCESS('Data import completed successfully!'))
        self.print_summary()
    
    def import_malaria_lab_tests(self, models_dir):
        """Import malaria lab test data (malaria lab test.csv)"""
        file_path = os.path.join(models_dir, 'malaria lab test.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'Importing malaria lab tests from {file_path}...')
        
        # Read CSV using pandas (same as notebook)
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
        
        # Delete existing malaria data
        LabTest.objects.filter(disease='MALARIA').delete()
        
        # Bulk create
        lab_tests = []
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['positive_tests']):
                lab_tests.append(LabTest(
                    date=row['date'],
                    disease='MALARIA',
                    positive_tests=int(row['positive_tests'])
                ))
        
        LabTest.objects.bulk_create(lab_tests, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {len(lab_tests)} malaria lab test records'))
    
    def import_dengue_lab_tests(self, models_dir):
        """Import dengue lab test data (dengue lab test.csv)"""
        file_path = os.path.join(models_dir, 'dengue lab test.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'Importing dengue lab tests from {file_path}...')
        
        # Read CSV using pandas - FORCE dayfirst=True (same as notebook)
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        
        # Delete existing dengue data
        LabTest.objects.filter(disease='DENGUE').delete()
        
        # Bulk create
        lab_tests = []
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['positive_tests']):
                lab_tests.append(LabTest(
                    date=row['date'],
                    disease='DENGUE',
                    positive_tests=int(row['positive_tests'])
                ))
        
        LabTest.objects.bulk_create(lab_tests, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {len(lab_tests)} dengue lab test records'))
    
    def import_pharmacy_sales(self, models_dir):
        """Import pharmacy sales data from all 4 CSV files"""
        
        # Delete all existing pharmacy sales
        PharmacySales.objects.all().delete()
        
        all_sales = []
        
        # 1. pharmacy.csv (2023 malaria medicines)
        self.import_pharmacy_2023(models_dir, all_sales)
        
        # 2. Jinnah Pharmacy 2.csv (2024 malaria medicines)
        self.import_jinnah_pharmacy_2(models_dir, all_sales)
        
        # 3. z1.csv (2023 dengue medicines)
        self.import_z1(models_dir, all_sales)
        
        # 4. Jinnah Pharmacy 4.csv (2024 dengue medicines)
        self.import_jinnah_pharmacy_4(models_dir, all_sales)
        
        # Bulk create all sales
        PharmacySales.objects.bulk_create(all_sales, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {len(all_sales)} pharmacy sales records'))
    
    def import_pharmacy_2023(self, models_dir, all_sales):
        """Import pharmacy.csv (2023 malaria: Coartem, Fansidar)"""
        file_path = os.path.join(models_dir, 'pharmacy.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'  Importing pharmacy.csv (2023 malaria medicines)...')
        
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
        
        # Filter for Coartem and Fansidar
        df = df[df['medicine'].isin(['Coartem', 'Fansidar'])]
        
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['sale']):
                all_sales.append(PharmacySales(
                    date=row['date'],
                    medicine=row['medicine'],
                    sale=float(row['sale']),
                    source='pharmacy.csv (2023)'
                ))
    
    def import_jinnah_pharmacy_2(self, models_dir, all_sales):
        """Import Jinnah Pharmacy 2.csv (2024 malaria: Coartem, Fansidar)"""
        file_path = os.path.join(models_dir, 'Jinnah Pharmacy 2.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'  Importing Jinnah Pharmacy 2.csv (2024 malaria medicines)...')
        
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
        
        # Filter for Coartem and Fansidar
        df = df[df['medicine'].isin(['Coartem', 'Fansidar'])]
        
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['sale']):
                all_sales.append(PharmacySales(
                    date=row['date'],
                    medicine=row['medicine'],
                    sale=float(row['sale']),
                    source='Jinnah Pharmacy 2.csv (2024)'
                ))
    
    def import_z1(self, models_dir, all_sales):
        """Import z1.csv (2023 dengue: Panadol, Calpol)"""
        file_path = os.path.join(models_dir, 'z1.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'  Importing z1.csv (2023 dengue medicines)...')
        
        df = pd.read_csv(file_path)
        
        # Rename columns (same as notebook)
        df.rename(columns={'Panadol_Sales': 'Panadol', 'Calpol_Sales': 'Calpol'}, inplace=True)
        
        # FORCE format to match (same as notebook)
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
        
        # Melt to long format
        for _, row in df.iterrows():
            if pd.notna(row['date']):
                if pd.notna(row['Panadol']):
                    all_sales.append(PharmacySales(
                        date=row['date'],
                        medicine='Panadol',
                        sale=float(row['Panadol']),
                        source='z1.csv (2023)'
                    ))
                if pd.notna(row['Calpol']):
                    all_sales.append(PharmacySales(
                        date=row['date'],
                        medicine='Calpol',
                        sale=float(row['Calpol']),
                        source='z1.csv (2023)'
                    ))
    
    def import_jinnah_pharmacy_4(self, models_dir, all_sales):
        """Import Jinnah Pharmacy 4.csv (2024 dengue: Panadol, Calpol)"""
        file_path = os.path.join(models_dir, 'Jinnah Pharmacy 4.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'  Importing Jinnah Pharmacy 4.csv (2024 dengue medicines)...')
        
        df = pd.read_csv(file_path)
        
        # Rename columns (same as notebook)
        df.rename(columns={'brand_name': 'medicine', 'total_sales': 'sale'}, inplace=True)
        
        # FORCE dayfirst=True (same as notebook)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        
        # Filter for Panadol and Calpol
        df = df[df['medicine'].isin(['Panadol', 'Calpol'])]
        
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['sale']):
                all_sales.append(PharmacySales(
                    date=row['date'],
                    medicine=row['medicine'],
                    sale=float(row['sale']),
                    source='Jinnah Pharmacy 4.csv (2024)'
                ))
    
    def print_summary(self):
        """Print summary of imported data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATA IMPORT SUMMARY'))
        self.stdout.write('='*50)
        
        malaria_count = LabTest.objects.filter(disease='MALARIA').count()
        dengue_count = LabTest.objects.filter(disease='DENGUE').count()
        
        self.stdout.write(f'\nLab Test Data:')
        self.stdout.write(f'  - Malaria: {malaria_count} records')
        self.stdout.write(f'  - Dengue: {dengue_count} records')
        
        coartem_count = PharmacySales.objects.filter(medicine='Coartem').count()
        fansidar_count = PharmacySales.objects.filter(medicine='Fansidar').count()
        panadol_count = PharmacySales.objects.filter(medicine='Panadol').count()
        calpol_count = PharmacySales.objects.filter(medicine='Calpol').count()
        
        self.stdout.write(f'\nPharmacy Sales Data:')
        self.stdout.write(f'  - Coartem: {coartem_count} records')
        self.stdout.write(f'  - Fansidar: {fansidar_count} records')
        self.stdout.write(f'  - Panadol: {panadol_count} records')
        self.stdout.write(f'  - Calpol: {calpol_count} records')
        
        self.stdout.write('\n' + '='*50)
