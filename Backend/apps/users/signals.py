from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import EmailVerificationToken, UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profiles(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

        from apps.gamification.models import UserGameProfile

        UserGameProfile.objects.get_or_create(user=instance)

        # create email verification token
        EmailVerificationToken.objects.create(
            user=instance,
            expires_at=timezone.now() + timedelta(hours=24),
        )
