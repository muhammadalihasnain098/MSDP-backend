"""
Users App - Handles authentication and user management

This app provides:
- Custom User model with role-based access (Admin, Health Official, etc.)
- JWT authentication endpoints (login, signup, refresh token)
- User profile management
- Permission-based API access

For learning:
- Custom User model extends AbstractUser
- JWT tokens are used instead of session-based auth (better for APIs)
- Roles are defined as choices in the model
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User Model
    
    Extends Django's built-in User model to add:
    - Role-based access control
    - Additional profile fields
    
    Roles:
    - ADMIN: Full system access
    - HEALTH_OFFICIAL: Can view forecasts and reports
    - LAB_TECH: Can enter lab data
    - PHARMACIST: Can enter pharmacy sales data
    """
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('HEALTH_OFFICIAL', 'Health Official'),
        ('LAB_TECH', 'Laboratory Technician'),
        ('PHARMACIST', 'Pharmacist'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='HEALTH_OFFICIAL'
    )
    
    phone = models.CharField(max_length=15, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'ADMIN'
    
    def is_health_official(self):
        """Check if user is a health official"""
        return self.role == 'HEALTH_OFFICIAL'
