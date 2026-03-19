from django.conf import settings
from django.db import models


class Badge(models.Model):
    CONDITION_CHOICES = [
        ('first_quiz',   'First Quiz Completed'),
        ('streak_5',     '5 Day Streak'),
        ('perfect_hard', 'Perfect Score on Hard'),
        ('five_topics',  '5 Different Topics'),
        ('comeback',     'Comeback After 3 Fails'),
        ('speed_demon',  'Finish in Half Time'),
        ('century',      '100 Quizzes Completed'),
    ]

    name           = models.CharField(max_length=100, unique=True)
    description    = models.TextField()
    icon_key       = models.CharField(max_length=50)
    condition_type = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'badges'

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user      = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                    related_name='earned_badges'
                )
    badge     = models.ForeignKey(
                    Badge,
                    on_delete=models.CASCADE,
                    related_name='awarded_to'
                )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'user_badges'
        unique_together = [['user', 'badge']]

    def __str__(self):
        return f"{self.user.email} earned {self.badge.name}"


class UserGameProfile(models.Model):
    LEVEL_CHOICES = [
        ('novice',     'Novice'),
        ('apprentice', 'Apprentice'),
        ('scholar',    'Scholar'),
        ('expert',     'Expert'),
        ('master',     'Master'),
    ]

    user                = models.OneToOneField(
                              settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='game_profile'
                          )
    xp_total            = models.IntegerField(default=0)
    level               = models.CharField(
                              max_length=15,
                              choices=LEVEL_CHOICES,
                              default='novice'
                          )
    streak_easy         = models.IntegerField(default=0)
    streak_medium       = models.IntegerField(default=0)
    streak_hard         = models.IntegerField(default=0)
    streak_freeze_count = models.IntegerField(default=1)
    last_easy_attempt   = models.DateField(null=True, blank=True)
    last_medium_attempt = models.DateField(null=True, blank=True)
    last_hard_attempt   = models.DateField(null=True, blank=True)
    last_active_date    = models.DateField(null=True, blank=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_game_profiles'

    def __str__(self):
        return f"{self.user.email} — {self.level} ({self.xp_total} XP)"


class PersonalBest(models.Model):
    user        = models.ForeignKey(
                      settings.AUTH_USER_MODEL,
                      on_delete=models.CASCADE,
                      related_name='personal_bests'
                  )
    topic       = models.ForeignKey(
                      'quizzes.Topic',
                      on_delete=models.CASCADE,
                      related_name='personal_bests'
                  )
    difficulty  = models.CharField(max_length=10)
    best_score  = models.FloatField()
    attempt     = models.ForeignKey(
                      'attempts.QuizAttempt',
                      on_delete=models.SET_NULL,
                      null=True,
                      related_name='personal_best_records'
                  )
    achieved_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'personal_bests'
        unique_together = [['user', 'topic', 'difficulty']]

    def __str__(self):
        return (
            f"{self.user.email} — {self.topic.name}"
            f" [{self.difficulty}] {self.best_score}%"
        )


class UserTopicStat(models.Model):
    user              = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name='topic_stats'
                        )
    topic             = models.ForeignKey(
                            'quizzes.Topic',
                            on_delete=models.CASCADE,
                            related_name='user_stats'
                        )
    total_attempts    = models.IntegerField(default=0)
    total_correct     = models.IntegerField(default=0)
    total_questions   = models.IntegerField(default=0)
    avg_score         = models.FloatField(default=0.0)
    best_score        = models.FloatField(default=0.0)
    last_attempted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table        = 'user_topic_stats'
        unique_together = [['user', 'topic']]

    def __str__(self):
        return f"{self.user.email} — {self.topic.name} avg: {self.avg_score}%"