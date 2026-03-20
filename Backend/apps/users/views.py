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


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # recent attempts
        from apps.attempts.models import QuizAttempt
        recent_attempts = QuizAttempt.objects.filter(
            user=user,
            status='submitted'
        ).select_related(
            'quiz__topic'
        ).order_by('-submitted_at')[:5]

        from apps.attempts.serializers import AttemptHistorySerializer
        attempts_data = AttemptHistorySerializer(
            recent_attempts, many=True
        ).data

        # stats
        from django.db.models import Avg, Count
        stats = QuizAttempt.objects.filter(
            user=user,
            status='submitted'
        ).aggregate(
            total_attempts=Count('id'),
            avg_score=Avg('percentage'),
            total_xp=Count('xp_earned'),
        )

        return success_response(data={
            'user': {
                'id':         user.id,
                'email':      user.email,
                'username':   user.username,
                'role':       user.role,
            },
            'stats': {
                'total_attempts': stats['total_attempts'] or 0,
                'avg_score':      round(stats['avg_score'] or 0, 2),
            },
            'recent_attempts': attempts_data,
        })

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return error_response(
                message='Admin access required',
                status_code=403
            )
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.select_related(
            'profile'
        ).order_by('-created_at')

        serializer = UserSerializer(users, many=True)
        return success_response(data=serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not request.user.is_admin:
            return error_response(
                message='Admin access required',
                status_code=403
            )
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.select_related('profile').get(id=user_id)
        except User.DoesNotExist:
            return error_response(message='User not found', status_code=404)

        serializer = UserSerializer(user)
        return success_response(data=serializer.data)

    def patch(self, request, user_id):
        if not request.user.is_admin:
            return error_response(
                message='Admin access required',
                status_code=403
            )
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(message='User not found', status_code=404)

        # only allow role and is_active changes
        allowed = ['role', 'is_active']
        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        return success_response(
            data=UserSerializer(user).data,
            message='User updated'
        )


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return error_response(
                message='Admin access required',
                status_code=403
            )

        from django.contrib.auth import get_user_model
        from apps.quizzes.models import Quiz
        from apps.attempts.models import QuizAttempt
        from apps.ai_generation.models import AIGenerationRequest
        from django.utils import timezone
        from django.db.models import Count

        User = get_user_model()
        today = timezone.now().date()

        total_users    = User.objects.count()
        total_quizzes  = Quiz.objects.filter(is_deleted=False).count()
        total_attempts_today = QuizAttempt.objects.filter(
            started_at__date=today
        ).count()
        ai_total       = AIGenerationRequest.objects.count()
        ai_success     = AIGenerationRequest.objects.filter(
            status='completed'
        ).count()
        ai_success_rate = round(
            (ai_success / ai_total * 100) if ai_total > 0 else 0, 2
        )

        return success_response(data={
            'total_users':           total_users,
            'total_quizzes':         total_quizzes,
            'total_attempts_today':  total_attempts_today,
            'ai_generation': {
                'total':        ai_total,
                'success':      ai_success,
                'success_rate': ai_success_rate,
            },
        })