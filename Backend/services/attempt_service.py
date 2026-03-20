from datetime import timedelta

from django.utils import timezone

from apps.attempts.models import AttemptAnswer, QuizAttempt
from apps.quizzes.models import Choice, Question, Quiz


def start_attempt(user, quiz_id):
    """
    Creates a new attempt for a user on a quiz.
    Checks if quiz exists, is published, user hasn't
    got an in_progress attempt, and has actual questions.
    Returns (attempt, error_message).
    """
    try:
        quiz = Quiz.objects.get(
            id=quiz_id,
            is_published=True,
            is_deleted=False,
        )
    except Quiz.DoesNotExist:
        return None, "Quiz not found or not available"

    # Fix 3 — use actual_question_count, not stored total_questions
    if quiz.actual_question_count == 0:
        return None, "Quiz has no questions yet"

    # check for existing in_progress attempt
    existing = QuizAttempt.objects.filter(
        user=user,
        quiz=quiz,
        status="in_progress",
    ).first()

    if existing:
        return existing, None

    # create new attempt — fix timezone.timedelta → timedelta
    attempt = QuizAttempt.objects.create(
        user=user,
        quiz=quiz,
        status="in_progress",
        expires_at=timezone.now() + timedelta(minutes=quiz.time_limit_minutes),
    )
    return attempt, None


def save_answer(attempt, question_id, choice_id):
    """
    Saves or updates an answer for a question in an attempt.
    is_correct calculated server side — never trusted from frontend.
    Returns (answer, error_message).
    """
    if attempt.status != "in_progress":
        return None, "Attempt is no longer active"

    if attempt.is_expired:
        attempt.status = "expired"
        attempt.save()
        return None, "Attempt has expired"

    try:
        question = Question.objects.get(
            id=question_id,
            quiz=attempt.quiz,
            is_deleted=False,
        )
    except Question.DoesNotExist:
        return None, "Question not found in this quiz"

    # validate choice belongs to question
    try:
        choice = Choice.objects.get(
            id=choice_id,
            question=question,
        )
    except Choice.DoesNotExist:
        return None, "Choice not found for this question"

    # calculate correctness server side
    is_correct = choice.is_correct
    marks_awarded = question.marks if is_correct else 0.0

    # update or create answer
    answer, _ = AttemptAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            "selected_choice": choice,
            "is_correct": is_correct,
            "marks_awarded": marks_awarded,
        },
    )
    return answer, None


def submit_attempt(attempt):
    """
    Finalises the attempt.
    Fix 4 — creates explicit skipped AttemptAnswer records for every
    unanswered question so the full picture is always in the DB.
    """
    if attempt.status != "in_progress":
        return attempt, "Attempt is already submitted or expired"

    all_questions = Question.objects.filter(
        quiz=attempt.quiz,
        is_deleted=False,
    )

    answered_ids = set(
        AttemptAnswer.objects.filter(
            attempt=attempt,
        ).values_list("question_id", flat=True)
    )

    # Fix 4 — create explicit skipped records for unanswered questions
    skipped = [
        AttemptAnswer(
            attempt=attempt,
            question=q,
            selected_choice=None,
            is_correct=False,
            marks_awarded=0.0,
        )
        for q in all_questions
        if q.id not in answered_ids
    ]
    if skipped:
        AttemptAnswer.objects.bulk_create(skipped)

    from services import scoring_service

    attempt, error = scoring_service.calculate_results(attempt)
    return attempt, error


def get_attempt_results(attempt):
    """
    Returns full results with correct answers and explanations.
    Only available after submission.
    """
    if attempt.status == "in_progress":
        return None, "Attempt not yet submitted"

    answers = (
        AttemptAnswer.objects.filter(
            attempt=attempt,
        )
        .select_related(
            "question",
            "selected_choice",
        )
        .prefetch_related("question__choices")
    )

    return answers, None


def get_user_attempts(user):
    """
    Returns all attempts for a user — history page.
    """
    return (
        QuizAttempt.objects.filter(user=user)
        .select_related("quiz", "quiz__topic")
        .order_by("-started_at")
    )


def validate_attempt_ownership(attempt, user):
    """
    Ensures the attempt belongs to the requesting user.
    """
    return attempt.user_id == user.id
