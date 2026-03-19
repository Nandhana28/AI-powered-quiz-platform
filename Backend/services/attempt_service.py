from django.utils import timezone
from apps.attempts.models import QuizAttempt, AttemptAnswer
from apps.quizzes.models import Quiz, Question, Choice


def start_attempt(user, quiz_id):
    """
    Creates a new attempt for a user on a quiz.
    Checks if quiz exists, is published, and user
    hasn't already got an in_progress attempt.
    Returns (attempt, error_message).
    """
    try:
        quiz = Quiz.objects.get(
            id=quiz_id,
            is_deleted=False,
            is_published=True
        )
    except Quiz.DoesNotExist:
        return None, 'Quiz not found or not available'

    # check for existing in_progress attempt
    existing = QuizAttempt.objects.filter(
        user=user,
        quiz=quiz,
        status='in_progress'
    ).first()

    if existing:
        return existing, None

    # create new attempt
    attempt = QuizAttempt.objects.create(
        user=user,
        quiz=quiz,
        status='in_progress',
        expires_at=timezone.now() + timezone.timedelta(
            minutes=quiz.time_limit_minutes
        )
    )
    return attempt, None


def save_answer(attempt, question_id, choice_id):
    """
    Saves or updates an answer for a question in an attempt.
    is_correct calculated server side — never trusted from frontend.
    Returns (answer, error_message).
    """
    if attempt.status != 'in_progress':
        return None, 'Attempt is no longer active'

    if attempt.is_expired:
        attempt.status = 'expired'
        attempt.save()
        return None, 'Attempt has expired'

    try:
        question = Question.objects.get(
            id=question_id,
            quiz=attempt.quiz,
            is_deleted=False
        )
    except Question.DoesNotExist:
        return None, 'Question not found in this quiz'

    # validate choice belongs to question
    try:
        choice = Choice.objects.get(
            id=choice_id,
            question=question
        )
    except Choice.DoesNotExist:
        return None, 'Choice not found for this question'

    # calculate correctness server side
    is_correct = choice.is_correct
    marks_awarded = question.marks if is_correct else 0.0

    # update or create answer
    answer, _ = AttemptAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'selected_choice': choice,
            'is_correct':      is_correct,
            'marks_awarded':   marks_awarded,
        }
    )
    return answer, None


def submit_attempt(attempt):
    """
    Submits the attempt and calculates final score.
    Returns (attempt, error_message).
    """
    if attempt.status != 'in_progress':
        return None, 'Attempt is already submitted or expired'

    from services.scoring_service import calculate_results
    attempt = calculate_results(attempt)
    return attempt, None


def get_attempt_results(attempt):
    """
    Returns full results with correct answers and explanations.
    Only available after submission.
    """
    if attempt.status == 'in_progress':
        return None, 'Attempt not yet submitted'

    answers = AttemptAnswer.objects.filter(
        attempt=attempt
    ).select_related(
        'question',
        'selected_choice',
        'question__choices'
    ).prefetch_related('question__choices')

    return answers, None


def get_user_attempts(user):
    """
    Returns all attempts for a user — history page.
    """
    return QuizAttempt.objects.filter(
        user=user
    ).select_related('quiz', 'quiz__topic').order_by('-started_at')


def validate_attempt_ownership(attempt, user):
    """
    Ensures the attempt belongs to the requesting user.
    """
    return attempt.user_id == user.id