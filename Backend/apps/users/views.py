from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    UserProfileSerializer,
)
from services import auth_service

User = get_user_model()


def success_response(data=None, message='Success', status_code=200):
    return Response({
        'success': True,
        'message': message,
        'data':    data,
    }, status=status_code)


def error_response(message='Error', errors=None, status_code=400):
    return Response({
        'success': False,
        'message': message,
        'errors':  errors,
    }, status=status_code)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors,
                status_code=400
            )
        user = serializer.save()
        return success_response(
            data={
                'id':       user.id,
                'email':    user.email,
                'username': user.username,
            },
            message='Account created successfully',
            status_code=201
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user, tokens = auth_service.login_user(email, password, request)

        if not user:
            return error_response(
                message='Invalid email or password',
                status_code=401
            )

        return success_response(
            data={
                'access':   tokens['access'],
                'refresh':  tokens['refresh'],
                'user': {
                    'id':    user.id,
                    'email': user.email,
                    'role':  user.role,
                }
            },
            message='Login successful'
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Refresh token required',
                errors=serializer.errors
            )

        success = auth_service.logout_user(
            serializer.validated_data['refresh']
        )

        if not success:
            return error_response(
                message='Invalid or expired token',
                status_code=400
            )

        return success_response(message='Logged out successfully')


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        email = serializer.validated_data['email']
        token = auth_service.generate_password_reset_token(email)

        # always return success — never reveal if email exists
        return success_response(
            message='If this email exists, a reset token has been sent.',
            data={'token': token} if token else None
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        success, result = auth_service.reset_password(
            token_string=str(serializer.validated_data['token']),
            new_password=serializer.validated_data['new_password']
        )

        if not success:
            return error_response(message=result, status_code=400)

        return success_response(message='Password reset successful')


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        success, error = auth_service.change_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password']
        )

        if not success:
            return error_response(message=error, status_code=400)

        return success_response(message='Password changed successfully')


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(data=serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message='Validation failed',
                errors=serializer.errors
            )
        serializer.save()
        return success_response(
            data=serializer.data,
            message='Profile updated successfully'
        )