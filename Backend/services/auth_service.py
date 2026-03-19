import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def register_user(validated_data):
    """
    Creates user with hashed password.
    Signal auto-creates UserProfile on save.
    """
    user = User.objects.create_user(
        username=validated_data['username'],
        email=validated_data['email'],
        password=validated_data['password'],
        role=validated_data.get('role', 'user'),
    )
    return user


def login_user(email, password, request=None):
    """
    Authenticates user and returns JWT tokens.
    Records login attempt in UserLoginHistory.
    Returns (user, tokens_dict) or (None, None) if invalid.
    """
    from apps.users.models import UserLoginHistory

    ip_address = _get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

    user = authenticate(username=email, password=password)

    if not user:
        # log failed attempt
        UserLoginHistory.objects.create(
            email_attempted=email,
            status='failed',
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, None

    if not user.is_active:
        UserLoginHistory.objects.create(
            user=user,
            email_attempted=email,
            status='blocked',
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, None

    # log success
    UserLoginHistory.objects.create(
        user=user,
        email_attempted=email,
        status='success',
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
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
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
    """
    Creates a password reset token for the user.
    Invalidates all previous unused tokens for same user.
    Returns token string or None if user not found.
    """
    from apps.users.models import PasswordResetToken

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return None

    # invalidate old tokens
    PasswordResetToken.objects.filter(
        user=user,
        is_used=False
    ).update(is_used=True)

    # create new token — expires in 15 minutes
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(minutes=15)
    )
    return str(token.token)


def reset_password(token_string, new_password):
    """
    Validates token and resets password.
    Returns (True, user) on success or (False, error_message) on failure.
    """
    from apps.users.models import PasswordResetToken

    try:
        token = PasswordResetToken.objects.select_related('user').get(
            token=token_string
        )
    except PasswordResetToken.DoesNotExist:
        return False, 'Invalid token'

    if not token.is_valid:
        return False, 'Token has expired or already been used'

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
        return False, 'Current password is incorrect'
    user.set_password(new_password)
    user.save()
    return True, None


def _get_client_ip(request):
    """
    Extracts real client IP — handles proxies.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')