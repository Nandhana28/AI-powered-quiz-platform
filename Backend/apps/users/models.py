import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user',  'User'),
        ('admin', 'Admin'),
    ]

    email      = models.EmailField(unique=True)
    role       = models.CharField(
                     max_length=10,
                     choices=ROLE_CHOICES,
                     default='user'
                 )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'


class UserProfile(models.Model):
    user         = models.OneToOneField(
                       User,
                       on_delete=models.CASCADE,
                       related_name='profile'
                   )
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url   = models.URLField(blank=True)
    bio          = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_deleted   = models.BooleanField(default=False)
    deleted_at   = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile — {self.user.email}"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


class PasswordResetToken(models.Model):
    user       = models.ForeignKey(
                     User,
                     on_delete=models.CASCADE,
                     related_name='password_reset_tokens'
                 )
    token      = models.UUIDField(
                     default=uuid.uuid4,
                     unique=True,
                     editable=False
                 )
    is_used    = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def mark_used(self):
        self.is_used = True
        self.save()


class UserLoginHistory(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed',  'Failed'),
        ('blocked', 'Blocked'),
    ]

    user             = models.ForeignKey(
                           User,
                           on_delete=models.CASCADE,
                           related_name='login_history',
                           null=True,
                           blank=True
                       )
    email_attempted  = models.EmailField()
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES)
    ip_address       = models.GenericIPAddressField(null=True, blank=True)
    user_agent       = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_login_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email_attempted} — {self.status}"