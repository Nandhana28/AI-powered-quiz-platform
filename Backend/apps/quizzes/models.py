from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Topic(models.Model):
    LEVEL_CHOICES = [
        (1, 'Domain'),
        (2, 'Subject'),
        (3, 'Subtopic'),
    ]

    name       = models.CharField(max_length=100)
    slug       = models.SlugField(max_length=200, unique=True)
    parent     = models.ForeignKey(
                     'self',
                     null=True,
                     blank=True,
                     on_delete=models.CASCADE,
                     related_name='children'
                 )
    level      = models.IntegerField(choices=LEVEL_CHOICES, default=3)
    icon_key   = models.CharField(max_length=50, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'topics'
        ordering        = ['level', 'name']
        unique_together = [['name', 'parent']]

    def __str__(self):
        return self.get_full_path()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_full_path())
        super().save(*args, **kwargs)

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()} / {self.name}"
        return self.name

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()


class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
    ]

    title               = models.CharField(max_length=200)
    description         = models.TextField(blank=True)
    topic               = models.ForeignKey(
                              Topic,
                              on_delete=models.CASCADE,
                              related_name='quizzes'
                          )
    difficulty          = models.CharField(
                              max_length=10,
                              choices=DIFFICULTY_CHOICES,
                              default='medium'
                          )
    total_questions     = models.IntegerField(default=10)
    time_limit_minutes  = models.IntegerField(default=15)
    pass_percentage     = models.FloatField(default=60.0)
    instructions        = models.TextField(blank=True)
    is_published        = models.BooleanField(default=False)
    is_ai_generated     = models.BooleanField(default=False)
    available_from      = models.DateTimeField(null=True, blank=True)
    expires_at          = models.DateTimeField(null=True, blank=True)
    is_deleted          = models.BooleanField(default=False)
    deleted_at          = models.DateTimeField(null=True, blank=True)
    created_by          = models.ForeignKey(
                              settings.AUTH_USER_MODEL,
                              on_delete=models.SET_NULL,
                              null=True,
                              related_name='created_quizzes'
                          )
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quizzes'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['topic', 'difficulty']),
            models.Index(fields=['is_published', 'is_deleted']),
        ]

    def __str__(self):
        return f"{self.title} [{self.difficulty}]"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @property
    def is_available(self):
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return self.is_published and not self.is_deleted


class Question(models.Model):
    quiz        = models.ForeignKey(
                      Quiz,
                      on_delete=models.CASCADE,
                      related_name='questions'
                  )
    text        = models.TextField()
    explanation = models.TextField(blank=True)
    order       = models.PositiveIntegerField(default=0)
    marks       = models.FloatField(default=1.0)
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questions'
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


class Choice(models.Model):
    question   = models.ForeignKey(
                     Question,
                     on_delete=models.CASCADE,
                     related_name='choices'
                 )
    text       = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'choices'
        ordering = ['order']

    def __str__(self):
        marker = '[CORRECT] ' if self.is_correct else ''
        return f"{marker}{self.text[:50]}"