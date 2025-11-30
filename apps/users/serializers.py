"""
User Serializers

Serializers convert Python objects (models) to JSON and vice versa.
They also handle validation.

For learning:
- ModelSerializer automatically creates fields from the model
- Extra kwargs control field behavior (write_only for passwords)
- create() method handles password hashing
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (read-only profile data)"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'role', 'phone', 'organization', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration (signup)"""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role', 'phone', 'organization']

    def create(self, validated_data):
        """Create user with hashed password and auto-generated username from email"""
        # Generate username from email (part before @)
        email = validated_data['email']
        username = email.split('@')[0]
        
        # Make username unique if it already exists
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'HEALTH_OFFICIAL'),
            phone=validated_data.get('phone', ''),
            organization=validated_data.get('organization', ''),
        )
        return user