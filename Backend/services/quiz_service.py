from django.utils import timezone
from django.utils.text import slugify

from apps.quizzes.models import Choice, Question, Quiz, Topic


def get_all_topics():
    return Topic.objects.filter(is_active=True).order_by("level", "name")


def get_topic_children(parent_id):
    return Topic.objects.filter(parent_id=parent_id, is_active=True).order_by("name")


def get_topic_by_id(topic_id):
    try:
        return Topic.objects.get(id=topic_id, is_active=True)
    except Topic.DoesNotExist:
        return None


def create_topic(name, level, parent_id=None, icon_key=""):
    parent = None
    if parent_id:
        parent = get_topic_by_id(parent_id)

    slug = slugify(f"{parent.get_full_path()} {name}" if parent else name)

    # ensure unique slug
    base_slug = slug
    counter = 1
    while Topic.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return Topic.objects.create(
        name=name,
        slug=slug,
        parent=parent,
        level=level,
        icon_key=icon_key,
    )


def get_all_quizzes(filters=None):
    queryset = Quiz.objects.filter(is_deleted=False, is_published=True).select_related(
        "topic", "created_by"
    )

    if filters:
        if filters.get("topic_id"):
            queryset = queryset.filter(topic_id=filters["topic_id"])
        if filters.get("difficulty"):
            queryset = queryset.filter(difficulty=filters["difficulty"])
        if filters.get("is_ai_generated") is not None:
            queryset = queryset.filter(is_ai_generated=filters["is_ai_generated"])

    return queryset.order_by("-created_at")


def get_quiz_by_id(quiz_id):
    try:
        return Quiz.objects.select_related("topic", "created_by").get(
            id=quiz_id, is_deleted=False
        )
    except Quiz.DoesNotExist:
        return None


def get_quiz_with_questions(quiz_id):
    try:
        return Quiz.objects.prefetch_related("questions__choices").get(
            id=quiz_id, is_deleted=False
        )
    except Quiz.DoesNotExist:
        return None


def create_quiz(data, created_by):
    return Quiz.objects.create(
        title=data["title"],
        description=data.get("description", ""),
        topic_id=data["topic_id"],
        difficulty=data["difficulty"],
        total_questions=data.get("total_questions", 10),
        time_limit_minutes=data.get("time_limit_minutes", 15),
        pass_percentage=data.get("pass_percentage", 60.0),
        instructions=data.get("instructions", ""),
        is_published=data.get("is_published", False),
        created_by=created_by,
    )


def update_quiz(quiz, data):
    allowed_fields = [
        "title",
        "description",
        "difficulty",
        "time_limit_minutes",
        "pass_percentage",
        "instructions",
        "is_published",
        "expires_at",
    ]
    for field in allowed_fields:
        if field in data:
            setattr(quiz, field, data[field])
    quiz.save()
    return quiz


def validate_question_choices(question):
    """
    Called after all choices are saved.
    Raises ValueError if constraints violated.
    """
    choices = question.choices.all()
    total = choices.count()
    correct = choices.filter(is_correct=True).count()

    if total != 4:
        question.soft_delete()
        raise ValueError(f"Question must have exactly 4 choices, got {total}")
    if correct != 1:
        question.soft_delete()
        raise ValueError(f"Question must have exactly 1 correct choice, got {correct}")


def soft_delete_quiz(quiz):
    quiz.soft_delete()
    return True


def add_question_to_quiz(quiz, question_data):
    question = Question.objects.create(
        quiz=quiz,
        text=question_data["text"],
        explanation=question_data.get("explanation", ""),
        order=question_data.get("order", 0),
        marks=question_data.get("marks", 1.0),
    )
    for choice_data in question_data.get("choices", []):
        Choice.objects.create(
            question=question,
            text=choice_data["text"],
            is_correct=choice_data.get("is_correct", False),
            order=choice_data.get("order", 0),
        )
    return question
