import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler

from services import auth_service

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)

User = get_user_model()


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "message": "An error occurred",
            "errors": response.data,
            "status_code": response.status_code,
        }
    return response


def success_response(data=None, message="Success", status_code=200):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(message="Error", errors=None, status_code=400):
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors,
        },
        status=status_code,
    )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed", errors=serializer.errors, status_code=400
            )
        user = serializer.save()
        return success_response(
            data={
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
            message="Account created. Please verify your email.",
            status_code=201,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Validation failed", errors=serializer.errors)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user, tokens = auth_service.login_user(email, password, request)

        if not user:
            return error_response(message="Invalid email or password", status_code=401)

        return success_response(
            data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
            },
            message="Login successful",
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Refresh token required", errors=serializer.errors
            )

        success = auth_service.logout_user(serializer.validated_data["refresh"])

        if not success:
            return error_response(message="Invalid or expired token", status_code=400)

        return success_response(message="Logged out successfully")


class PasswordResetRequestView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return error_response(message="Email required", status_code=400)

        try:
            auth_service.generate_password_reset_token(email)
        except ValueError as e:
            return error_response(message=str(e), status_code=429)

        # always return success to avoid email enumeration
        return success_response(
            message="If that email exists, a reset link has been sent"
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Validation failed", errors=serializer.errors)

        success, result = auth_service.reset_password(
            token_string=str(serializer.validated_data["token"]),
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return error_response(message=result, status_code=400)

        return success_response(message="Password reset successful")


class VerifyEmailView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return error_response(message="Token required", status_code=400)

        try:
            user = auth_service.verify_email(token)
            return success_response(
                message="Email verified successfully", data={"email": user.email}
            )
        except ValueError as e:
            return error_response(message=str(e), status_code=400)


class ResendVerificationView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return error_response(message="Email required", status_code=400)

        try:
            user = User.objects.get(email=email, is_active=False)
            token = user.email_verification
            token.token = uuid.uuid4()
            token.expires_at = timezone.now() + timedelta(hours=24)
            token.save()

            verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
            from django.core.mail import send_mail

            send_mail(
                subject="Verify your email — QuizApp",
                message=(
                    f"New verification link:\n\n{verify_url}"
                    f"\n\nExpires in 24 hours."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            return success_response(message="Verification email resent")
        except User.DoesNotExist:
            return success_response(
                message="If that email exists, a link has been sent"
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Validation failed", errors=serializer.errors)

        success, error = auth_service.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return error_response(message=error, status_code=400)

        return success_response(message="Password changed successfully")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(data=serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user.profile, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(message="Validation failed", errors=serializer.errors)
        serializer.save()
        return success_response(
            data=serializer.data, message="Profile updated successfully"
        )


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        from django.db.models import Avg, Count

        from apps.attempts.models import QuizAttempt
        from apps.attempts.serializers import AttemptHistorySerializer

        recent_attempts = (
            QuizAttempt.objects.filter(user=user, status="submitted")
            .select_related("quiz__topic")
            .order_by("-submitted_at")[:5]
        )
        attempts_data = AttemptHistorySerializer(recent_attempts, many=True).data

        stats = QuizAttempt.objects.filter(user=user, status="submitted").aggregate(
            total_attempts=Count("id"),
            avg_score=Avg("percentage"),
        )

        return success_response(
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                },
                "stats": {
                    "total_attempts": stats["total_attempts"] or 0,
                    "avg_score": round(stats["avg_score"] or 0, 2),
                },
                "recent_attempts": attempts_data,
            }
        )


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return error_response(message="Admin access required", status_code=403)

        users = User.objects.select_related("profile").order_by("-created_at")
        serializer = UserSerializer(users, many=True)
        return success_response(data=serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not request.user.is_admin:
            return error_response(message="Admin access required", status_code=403)
        try:
            user = User.objects.select_related("profile").get(id=user_id)
        except User.DoesNotExist:
            return error_response(message="User not found", status_code=404)

        serializer = UserSerializer(user)
        return success_response(data=serializer.data)

    def patch(self, request, user_id):
        if not request.user.is_admin:
            return error_response(message="Admin access required", status_code=403)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(message="User not found", status_code=404)

        allowed = ["role", "is_active"]
        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        return success_response(data=UserSerializer(user).data, message="User updated")


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return error_response(message="Admin access required", status_code=403)

        from apps.ai_generation.models import AIGenerationRequest
        from apps.attempts.models import QuizAttempt
        from apps.quizzes.models import Quiz

        today = timezone.now().date()

        total_users = User.objects.count()
        total_quizzes = Quiz.objects.filter(is_deleted=False).count()
        total_attempts_today = QuizAttempt.objects.filter(
            started_at__date=today
        ).count()
        ai_total = AIGenerationRequest.objects.count()
        ai_success = AIGenerationRequest.objects.filter(status="completed").count()
        ai_success_rate = round((ai_success / ai_total * 100) if ai_total > 0 else 0, 2)

        return success_response(
            data={
                "total_users": total_users,
                "total_quizzes": total_quizzes,
                "total_attempts_today": total_attempts_today,
                "ai_generation": {
                    "total": ai_total,
                    "success": ai_success,
                    "success_rate": ai_success_rate,
                },
            }
        )
