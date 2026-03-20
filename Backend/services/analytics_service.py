from django.db.models import Avg, Count, Max
from django.utils import timezone


def update_topic_stat(user, topic, score, attempt):
    """
    Updates running stats for user+topic after every submission.
    Called after every submit — avoids expensive aggregations later.
    """
    from apps.gamification.models import UserTopicStat

    stat, created = UserTopicStat.objects.get_or_create(
        user=user,
        topic=topic,
        defaults={
            'total_attempts':  1,
            'total_correct':   attempt.correct_count or 0,
            'total_questions': attempt.total_marks or 0,
            'avg_score':       score,
            'best_score':      score,
            'last_attempted_at': timezone.now(),
        }
    )

    if not created:
        # running average formula
        new_total   = stat.total_attempts + 1
        new_avg     = (
            (stat.avg_score * stat.total_attempts + score) / new_total
        )
        stat.total_attempts   = new_total
        stat.total_correct   += attempt.correct_count or 0
        stat.total_questions += attempt.total_marks or 0
        stat.avg_score        = round(new_avg, 2)
        stat.best_score       = max(stat.best_score, score)
        stat.last_attempted_at = timezone.now()
        stat.save()

    return stat


def calculate_percentile(user, quiz, score):
    """
    Returns what percentage of users this score beats on this quiz.
    """
    from apps.attempts.models import QuizAttempt

    all_scores = QuizAttempt.objects.filter(
        quiz=quiz,
        status='submitted'
    ).values_list('percentage', flat=True)

    total = len(all_scores)
    if total == 0:
        return 100

    below = sum(1 for s in all_scores if s < score)
    return round((below / total) * 100, 1)


def suggest_difficulty(user, topic):
    """
    Suggests next difficulty based on recent performance.
    >80% avg on current → suggest harder
    <40% avg on current → suggest easier
    """
    from apps.attempts.models import QuizAttempt

    recent = QuizAttempt.objects.filter(
        user=user,
        quiz__topic=topic,
        status='submitted'
    ).order_by('-submitted_at')[:5]

    if not recent:
        return None

    avg = sum(a.percentage for a in recent) / len(recent)
    current_difficulty = recent[0].quiz.difficulty

    if avg > 80 and current_difficulty != 'hard':
        next_map = {'easy': 'medium', 'medium': 'hard'}
        return next_map.get(current_difficulty)

    if avg < 40 and current_difficulty != 'easy':
        prev_map = {'hard': 'medium', 'medium': 'easy'}
        return prev_map.get(current_difficulty)

    return None


def get_leaderboard(topic_id=None, difficulty=None, limit=10):
    """
    Returns top users by XP globally or filtered.
    """
    from apps.gamification.models import UserGameProfile

    queryset = UserGameProfile.objects.select_related(
        'user'
    ).order_by('-xp_total')[:limit]

    return [
        {
            'rank':     i + 1,
            'username': p.user.username,
            'level':    p.level,
            'xp_total': p.xp_total,
        }
        for i, p in enumerate(queryset)
    ]