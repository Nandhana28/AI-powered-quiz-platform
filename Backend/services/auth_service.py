import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import EmailVerificationToken

User = get_user_model()


def register_user(username, email, password):
    if User.objects.filter(email=email).exists():
        raise ValueError("Email already registered")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=False,  # inactive until email verified
    )

    # send verification email
    try:
        token = user.email_verification
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
        from django.core.mail import send_mail

        send_mail(
            subject="Verify your email — QuizApp",
            message=f"Click to verify your email:\n\n{verify_url}\n\nExpires in 24 hours.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass

    return user


def verify_email(token_str):
    try:
        token = EmailVerificationToken.objects.select_related("user").get(
            token=token_str
        )
    except EmailVerificationToken.DoesNotExist:
        raise ValueError("Invalid verification token")

    if token.is_verified:
        raise ValueError("Email already verified")

    if token.is_expired:
        raise ValueError("Verification token expired — request a new one")

    token.is_verified = True
    token.save()

    token.user.is_active = True
    token.user.save()

    return token.user


def login_user(email, password, request=None):
    """
    Authenticates user and returns JWT tokens.
    Records login attempt in UserLoginHistory.
    Returns (user, tokens_dict) or (None, None) if invalid.
    """
    from apps.users.models import UserLoginHistory

    ip_address = _get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "") if request else ""

    user = authenticate(username=email, password=password)

    if not user:
        UserLoginHistory.objects.create(
            email_attempted=email,
            status="failed",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, None

    if not user.is_active:
        UserLoginHistory.objects.create(
            user=user,
            email_attempted=email,
            status="blocked",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, None

    UserLoginHistory.objects.create(
        user=user,
        email_attempted=email,
        status="success",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    tokens = get_tokens_for_user(user)
    return user, tokens


def get_tokens_for_user(user):
    """
    Generates JWT access and refresh tokens for a user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def logout_user(refresh_token):
    """
    Blacklists the refresh token — invalidates the session.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return True
    except Exception:
        return False


def generate_password_reset_token(email):
    from django.core.mail import send_mail

    from apps.users.models import PasswordResetToken

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return None

    # Fix 5 — rate limit: max 3 reset requests per hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_count = PasswordResetToken.objects.filter(
        user=user,
        created_at__gte=one_hour_ago,
    ).count()

    if recent_count >= 3:
        raise ValueError(
            "Too many password reset requests. Please wait before trying again."
        )

    # invalidate old tokens
    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

    # create new token
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(minutes=15),
    )

    # send email
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
    try:
        send_mail(
            subject="Password Reset Request — QuizApp",
            message=(
                f"Click the link to reset your password:\n\n{reset_url}"
                f"\n\nThis link expires in 15 minutes."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass

    return str(token.token)


def reset_password(token_string, new_password):
    """
    Validates token and resets password.
    Returns (True, user) on success or (False, error_message) on failure.
    """
    from apps.users.models import PasswordResetToken

    try:
        token = PasswordResetToken.objects.select_related("user").get(
            token=token_string
        )
    except PasswordResetToken.DoesNotExist:
        return False, "Invalid token"

    if not token.is_valid:
        return False, "Token has expired or already been used"

    user = token.user
    user.set_password(new_password)
    user.save()
    token.mark_used()
    return True, user


def change_password(user, old_password, new_password):
    """
    Changes password after verifying the old one.
    Returns (True, None) or (False, error_message).
    """
    if not user.check_password(old_password):
        return False, "Current password is incorrect"
    user.set_password(new_password)
    user.save()
    return True, None


def _get_client_ip(request):
    """
    Extracts real client IP — handles proxies.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
