"""
User Views (API Endpoints)

Views handle HTTP requests and return responses.

For learning:
- APIView: Basic class-based view
- POST /api/users/register/ - Create new user account
- POST /api/users/login/ - Get JWT tokens
- POST /api/users/refresh/ - Refresh access token
- GET /api/users/profile/ - Get current user profile
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .serializers import UserRegistrationSerializer, UserSerializer


class RegisterView(APIView):
    """
    User Registration Endpoint
    POST /api/users/register/

    Public endpoint (no authentication required)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)

        # Log validation errors for debugging
        print(f"Registration validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LoginView(APIView):
    """
    User Login Endpoint
    POST /api/users/login/

    Public endpoint
    Request body: {email, password}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Try to find user by email (use first() to handle duplicates)
        from .models import User
        try:
            user_obj = User.objects.filter(email=email).first()
            if not user_obj:
                raise User.DoesNotExist
            # Authenticate using username (since that's the default USERNAME_FIELD)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })

        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
class ProfileView(APIView):
    """
    User Profile Endpoint
    GET /api/users/profile/
    
    Requires authentication (JWT token in header)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
