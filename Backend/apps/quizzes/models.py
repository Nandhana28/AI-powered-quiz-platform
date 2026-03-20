from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Topic(models.Model):
    LEVEL_CHOICES = [
        (1, "Domain"),
        (2, "Subject"),
        (3, "Subtopic"),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    level = models.IntegerField(choices=LEVEL_CHOICES, default=3)
    icon_key = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topics"
        ordering = ["level", "name"]
        unique_together = [["name", "parent"]]

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
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="quizzes")
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="medium"
    )
    total_questions = models.IntegerField(default=10)
    time_limit_minutes = models.IntegerField(default=15)
    pass_percentage = models.FloatField(default=60.0)
    instructions = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    is_ai_generated = models.BooleanField(default=False)  # Fix: removed duplicate
    is_weekly_challenge = models.BooleanField(default=False)
    weekly_bonus_xp = models.IntegerField(default=0)
    available_from = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quizzes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quizzes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["topic", "difficulty"]),
            models.Index(fields=["is_published", "is_deleted"]),
            models.Index(fields=["is_published", "is_deleted", "topic"]),
            models.Index(fields=["is_weekly_challenge", "is_published"]),
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

    @property
    def actual_question_count(self):
        """Fix 3 — always reflects real question count, never lies."""
        return self.questions.filter(is_deleted=False).count()

    @property
    def is_ready(self):
        """True only if published and has actual questions."""
        return (
            self.is_published and not self.is_deleted and self.actual_question_count > 0
        )


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    marks = models.FloatField(default=1.0)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "questions"
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def clean(self):
        """Fix 2 — validate choice counts at the model level."""
        if self.pk:
            correct_count = self.choices.filter(is_correct=True).count()
            total_count = self.choices.count()
            if total_count > 0 and correct_count != 1:
                raise ValidationError(
                    f"Question must have exactly 1 correct choice, found {correct_count}"
                )
            if total_count > 0 and total_count != 4:
                raise ValidationError(
                    f"Question must have exactly 4 choices, found {total_count}"
                )


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "choices"
        ordering = ["order"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(order__gte=0),
                name="choice_order_non_negative",
            ),
        ]

    def __str__(self):
        marker = "[CORRECT] " if self.is_correct else ""
        return f"{marker}{self.text[:50]}"

    def clean(self):
        """
        Fix 2 — prevent saving a second correct choice for the same question.
        Runs on full_clean() / admin saves / serializer .validate().
        A true DB-level unique constraint on is_correct=True requires a
        partial index — added via a migration RunSQL (see migrations).
        """
        if self.is_correct:
            qs = Choice.objects.filter(
                question=self.question,
                is_correct=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "A correct choice already exists for this question."
                )
