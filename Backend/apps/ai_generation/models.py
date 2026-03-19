from django.conf import settings
from django.db import models


class AIGenerationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
    ]

    requested_by   = models.ForeignKey(
                         settings.AUTH_USER_MODEL,
                         on_delete=models.CASCADE,
                         related_name='ai_generation_requests'
                     )
    topic          = models.ForeignKey(
                         'quizzes.Topic',
                         on_delete=models.CASCADE,
                         related_name='generation_requests'
                     )
    difficulty     = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    question_count = models.IntegerField(default=10)
    status         = models.CharField(
                         max_length=15,
                         choices=STATUS_CHOICES,
                         default='pending'
                     )
    error_message  = models.TextField(blank=True)
    retries        = models.IntegerField(default=0)
    max_retries    = models.IntegerField(default=3)
    raw_response   = models.JSONField(null=True, blank=True)
    quiz           = models.OneToOneField(
                         'quizzes.Quiz',
                         on_delete=models.SET_NULL,
                         null=True,
                         blank=True,
                         related_name='generation_request'
                     )
    prompt_used    = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    completed_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ai_generation_requests'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"AIRequest by {self.requested_by.email}"
            f" — {self.topic.name} [{self.status}]"
        )

    @property
    def can_retry(self):
        return self.retries < self.max_retries and self.status == 'failed'