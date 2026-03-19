from django.conf import settings
from django.db import models
from django.utils import timezone


class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted',   'Submitted'),
        ('expired',     'Expired'),
        ('abandoned',   'Abandoned'),
    ]

    user               = models.ForeignKey(
                             settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='attempts'
                         )
    quiz               = models.ForeignKey(
                             'quizzes.Quiz',
                             on_delete=models.CASCADE,
                             related_name='attempts'
                         )
    status             = models.CharField(
                             max_length=15,
                             choices=STATUS_CHOICES,
                             default='in_progress'
                         )
    score              = models.FloatField(null=True, blank=True)
    total_marks        = models.FloatField(null=True, blank=True)
    correct_count      = models.IntegerField(null=True, blank=True)
    incorrect_count    = models.IntegerField(null=True, blank=True)
    skipped_count      = models.IntegerField(null=True, blank=True)
    percentage         = models.FloatField(null=True, blank=True)
    is_passed          = models.BooleanField(null=True, blank=True)
    xp_earned          = models.IntegerField(null=True, blank=True)
    started_at         = models.DateTimeField(auto_now_add=True)
    submitted_at       = models.DateTimeField(null=True, blank=True)
    expires_at         = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    is_late_submission = models.BooleanField(default=False)

    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-started_at']
        indexes  = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.quiz.title} [{self.status}]"

    @property
    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def calculate_time_taken(self):
        if self.submitted_at and self.started_at:
            delta = self.submitted_at - self.started_at
            return int(delta.total_seconds())
        return None


class AttemptAnswer(models.Model):
    attempt         = models.ForeignKey(
                          QuizAttempt,
                          on_delete=models.CASCADE,
                          related_name='answers'
                      )
    question        = models.ForeignKey(
                          'quizzes.Question',
                          on_delete=models.CASCADE,
                          related_name='attempt_answers'
                      )
    selected_choice = models.ForeignKey(
                          'quizzes.Choice',
                          on_delete=models.SET_NULL,
                          null=True,
                          blank=True,
                          related_name='selected_in_answers'
                      )
    is_correct      = models.BooleanField(default=False)
    marks_awarded   = models.FloatField(default=0.0)
    answered_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'attempt_answers'
        unique_together = [['attempt', 'question']]

    def __str__(self):
        status = 'correct' if self.is_correct else 'wrong'
        return f"Attempt {self.attempt.id} — Q{self.question.order} [{status}]"