from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('created',        'Created'),
        ('updated',        'Updated'),
        ('deleted',        'Deleted'),
        ('attempted',      'Attempted'),
        ('submitted',      'Submitted'),
        ('generated',      'Generated'),
        ('login',          'Login'),
        ('logout',         'Logout'),
        ('password_reset', 'Password Reset'),
        ('role_changed',   'Role Changed'),
    ]

    actor         = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.SET_NULL,
                        null=True,
                        blank=True,
                        related_name='audit_logs'
                    )
    action        = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)
    resource_id   = models.IntegerField(null=True, blank=True)
    description   = models.TextField(blank=True)
    metadata      = models.JSONField(default=dict, blank=True)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    timestamp     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes  = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        actor = self.actor.email if self.actor else 'system'
        return f"{actor} — {self.action} {self.resource_type}"