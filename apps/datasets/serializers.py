"""
Dataset Serializers
"""

from rest_framework import serializers
from .models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for Dataset model"""
    
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.username',
        read_only=True
    )
    
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'description', 'file', 'uploaded_by',
                  'uploaded_by_name', 'status', 'row_count', 'column_count',
                  'validation_errors', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uploaded_by', 'status', 'row_count',
                            'column_count', 'validation_errors', 'created_at',
                            'updated_at']


class DatasetUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading datasets"""
    
    dataset_type = serializers.ChoiceField(choices=['LAB', 'PHARMACY'], write_only=True)
    disease = serializers.ChoiceField(choices=['MALARIA', 'DENGUE'], write_only=True)

    class Meta:
        model = Dataset
        fields = ['name', 'description', 'file', 'dataset_type', 'disease']

    def validate_file(self, value):
        """Validate file type and size"""
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = value.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 10MB")
        
        return value
    
    def create(self, validated_data):
        # Extract custom fields
        dataset_type = validated_data.pop('dataset_type')
        disease = validated_data.pop('disease')
        
        # Create dataset with additional metadata in description
        if not validated_data.get('description'):
            validated_data['description'] = f"{dataset_type} data for {disease}"
        
        # Store type and disease in the name for now
        validated_data['name'] = f"{validated_data.get('name', 'upload')} ({dataset_type} - {disease})"
        
        dataset = super().create(validated_data)
        
        # Store metadata for the task
        dataset.validation_errors = {
            'dataset_type': dataset_type,
            'disease': disease
        }
        dataset.save()
        
        return dataset