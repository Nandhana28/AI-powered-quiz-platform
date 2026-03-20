from django.utils import timezone

from apps.attempts.models import AttemptAnswer, QuizAttempt


def calculate_results(attempt):
    """
    Calculates and saves final score after submission.
    Called only from attempt_service.submit_attempt().
    """
    answers = AttemptAnswer.objects.filter(attempt=attempt).select_related("question")

    actual_question_count = attempt.quiz.actual_question_count
    answered = answers.filter(selected_choice__isnull=False).count()
    correct = answers.filter(is_correct=True).count()
    incorrect = answers.filter(is_correct=False, selected_choice__isnull=False).count()
    skipped = actual_question_count - answered

    total_marks = sum(a.question.marks for a in answers)
    score_earned = sum(a.marks_awarded for a in answers)
    percentage = round((score_earned / total_marks * 100) if total_marks > 0 else 0, 2)
    is_passed = percentage >= attempt.quiz.pass_percentage
    submitted_at = timezone.now()
    is_late = attempt.expires_at and submitted_at > attempt.expires_at
    time_taken = int((submitted_at - attempt.started_at).total_seconds())
    xp_earned = calculate_xp(percentage, attempt.quiz.difficulty)

    attempt.status = "submitted"
    attempt.score = score_earned
    attempt.total_marks = total_marks
    attempt.correct_count = correct
    attempt.incorrect_count = incorrect
    attempt.skipped_count = skipped
    attempt.percentage = percentage
    attempt.is_passed = is_passed
    attempt.submitted_at = submitted_at
    attempt.time_taken_seconds = time_taken
    attempt.is_late_submission = is_late
    attempt.xp_earned = xp_earned
    attempt.save()

    return attempt


def calculate_xp(percentage, difficulty):
    """
    XP based on score and difficulty.
    Easy=1x, Medium=1.5x, Hard=2x multiplier.
    """
    multipliers = {
        "easy": 1.0,
        "medium": 1.5,
        "hard": 2.0,
    }
    multiplier = multipliers.get(difficulty, 1.0)
    base_xp = int(percentage)
    return int(base_xp * multiplier)


def validate_attempt_ownership(attempt, user):
    """
    Ensures the attempt belongs to the requesting user.
    Returns True if owner, False if not.
    """
    return attempt.user_id == user.id
