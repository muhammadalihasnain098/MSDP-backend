"""
Datasets App - Handles lab test data and pharmacy sales data

This app stores the actual time-series data used for disease forecasting:
- LabTest: Daily positive test counts (malaria/dengue)
- PharmacySales: Daily medicine sales (Coartem, Fansidar, Panadol, Calpol)

Data is imported from CSV files and used by the forecasting models.
"""

from django.db import models
from django.conf import settings


class LabTest(models.Model):
    """
    Lab Test Data Model
    
    Stores daily positive test counts for diseases.
    Used as the target variable (y) in forecasting models.
    """
    
    DISEASE_CHOICES = [
        ('MALARIA', 'Malaria'),
        ('DENGUE', 'Dengue'),
        ('DIARRHOEA', 'Diarrhoea'),
    ]
    
    date = models.DateField()
    disease = models.CharField(max_length=20, choices=DISEASE_CHOICES)
    positive_tests = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date']
        unique_together = ['date', 'disease']
        indexes = [
            models.Index(fields=['date', 'disease']),
            models.Index(fields=['disease', 'date']),
        ]
    
    def __str__(self):
        return f"{self.disease} - {self.date}: {self.positive_tests} positive"


class PharmacySales(models.Model):
    """
    Pharmacy Sales Data Model
    
    Stores daily medicine sales data.
    Used as features (X) in forecasting models.
    Medicine names are automatically mapped to diseases during import.
    """
    
    DISEASE_CHOICES = [
        ('DENGUE', 'Dengue'),
        ('ANTIMALARIA', 'Anti-Malaria'),
        ('CHOLERA', 'Cholera'),
        ('DIARRHOEA', 'Diarrhoea'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    date = models.DateField()
    medicine = models.CharField(max_length=100)  # Medicine/brand name
    sale = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Auto-detected disease category based on medicine name
    disease_category = models.CharField(
        max_length=20, 
        choices=DISEASE_CHOICES,
        default='UNKNOWN',
        help_text='Automatically detected from medicine name'
    )
    
    # Optional: track data source for auditing
    source = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'medicine']
        unique_together = ['date', 'medicine']
        indexes = [
            models.Index(fields=['date', 'medicine']),
            models.Index(fields=['medicine', 'date']),
            models.Index(fields=['disease_category', 'date']),
        ]
    
    def __str__(self):
        return f"{self.medicine} ({self.disease_category}) - {self.date}: {self.sale}"


class Dataset(models.Model):
    """
    Dataset Model
    
    Stores metadata about uploaded datasets.
    Actual data files are stored in MEDIA_ROOT/datasets/
    """
    
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('VALIDATING', 'Validating'),
        ('VALID', 'Valid'),
        ('INVALID', 'Invalid'),
        ('PROCESSING', 'Processing'),
        ('PROCESSED', 'Processed'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='datasets/')
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPLOADED'
    )
    
    # Validation results
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    validation_errors = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"
