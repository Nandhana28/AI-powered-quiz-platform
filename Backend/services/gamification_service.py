from django.utils import timezone
from django.db.models import Avg


def update_streak(user, difficulty):
    """
    Updates streak for the given difficulty after a submission.
    Checks last attempt date:
    - same day     → no change
    - yesterday    → increment
    - gap > 1 day  → check freeze, else reset to 1
    """
    from apps.gamification.models import UserGameProfile

    profile, _ = UserGameProfile.objects.get_or_create(user=user)
    today       = timezone.now().date()

    date_field   = f'last_{difficulty}_attempt'
    streak_field = f'streak_{difficulty}'

    last_date = getattr(profile, date_field)
    streak    = getattr(profile, streak_field)

    if last_date is None:
        # first attempt ever on this difficulty
        setattr(profile, streak_field, 1)
    elif last_date == today:
        # already attempted today — no change
        pass
    elif (today - last_date).days == 1:
        # consecutive day — increment
        setattr(profile, streak_field, streak + 1)
    else:
        # gap — check freeze
        if profile.streak_freeze_count > 0:
            profile.streak_freeze_count -= 1
        else:
            setattr(profile, streak_field, 1)

    setattr(profile, date_field, today)
    profile.last_active_date = today
    profile.save()
    return profile


def award_xp(user, xp_earned):
    """
    Adds XP to user game profile and checks for level up.
    """
    from apps.gamification.models import UserGameProfile

    profile, _ = UserGameProfile.objects.get_or_create(user=user)
    profile.xp_total += xp_earned
    profile.save()

    check_level_up(profile)
    return profile


def check_level_up(profile):
    """
    Checks if user has crossed a level threshold and upgrades.
    Thresholds: novice=0, apprentice=500, scholar=1500,
                expert=3500, master=7000
    """
    thresholds = [
        (7000, 'master'),
        (3500, 'expert'),
        (1500, 'scholar'),
        (500,  'apprentice'),
        (0,    'novice'),
    ]

    for xp_required, level in thresholds:
        if profile.xp_total >= xp_required:
            if profile.level != level:
                profile.level = level
                profile.save()
            break

    return profile


def check_and_award_badges(user, attempt):
    """
    Runs all badge checks after a submission.
    Awards any newly earned badges.
    Returns list of newly earned badge names.
    """
    newly_earned = []

    checkers = [
        check_first_quiz_badge,
        check_streak_badge,
        check_perfect_hard_badge,
        check_polymath_badge,
        check_comeback_badge,
        check_speed_demon_badge,
    ]

    for checker in checkers:
        badge = checker(user, attempt)
        if badge:
            newly_earned.append(badge.name)

    return newly_earned


def _award_badge(user, condition_type):
    """
    Awards a badge if not already earned.
    Returns badge if newly awarded, None if already had it.
    """
    from apps.gamification.models import Badge, UserBadge

    try:
        badge = Badge.objects.get(
            condition_type=condition_type,
            is_active=True
        )
    except Badge.DoesNotExist:
        return None

    _, created = UserBadge.objects.get_or_create(
        user=user,
        badge=badge
    )
    return badge if created else None


def check_first_quiz_badge(user, attempt):
    from apps.attempts.models import QuizAttempt
    count = QuizAttempt.objects.filter(
        user=user, status='submitted'
    ).count()
    if count == 1:
        return _award_badge(user, 'first_quiz')
    return None


def check_streak_badge(user, attempt):
    from apps.gamification.models import UserGameProfile
    try:
        profile = UserGameProfile.objects.get(user=user)
        if any([
            profile.streak_easy   >= 5,
            profile.streak_medium >= 5,
            profile.streak_hard   >= 5,
        ]):
            return _award_badge(user, 'streak_5')
    except UserGameProfile.DoesNotExist:
        pass
    return None


def check_perfect_hard_badge(user, attempt):
    if attempt.percentage == 100.0 and attempt.quiz.difficulty == 'hard':
        return _award_badge(user, 'perfect_hard')
    return None


def check_polymath_badge(user, attempt):
    from apps.attempts.models import QuizAttempt
    distinct_topics = QuizAttempt.objects.filter(
        user=user,
        status='submitted'
    ).values('quiz__topic').distinct().count()
    if distinct_topics >= 5:
        return _award_badge(user, 'five_topics')
    return None


def check_comeback_badge(user, attempt):
    from apps.attempts.models import QuizAttempt
    recent = QuizAttempt.objects.filter(
        user=user,
        status='submitted'
    ).order_by('-submitted_at')[:4]

    attempts = list(recent)
    if len(attempts) < 4:
        return None

    # latest is index 0 — check it's good
    # previous 3 should be bad
    if attempts[0].percentage >= 70:
        if all(a.percentage < 50 for a in attempts[1:4]):
            return _award_badge(user, 'comeback')
    return None


def check_speed_demon_badge(user, attempt):
    if not attempt.time_taken_seconds:
        return None
    time_limit_seconds = attempt.quiz.time_limit_minutes * 60
    if attempt.time_taken_seconds < (time_limit_seconds * 0.5):
        return _award_badge(user, 'speed_demon')
    return None


def update_personal_best(user, topic, difficulty, score, attempt):
    """
    Updates personal best if new score is higher.
    Returns True if new best was set.
    """
    from apps.gamification.models import PersonalBest

    personal_best, created = PersonalBest.objects.get_or_create(
        user=user,
        topic=topic,
        difficulty=difficulty,
        defaults={
            'best_score': score,
            'attempt':    attempt,
        }
    )

    if not created and score > personal_best.best_score:
        personal_best.best_score = score
        personal_best.attempt    = attempt
        personal_best.save()
        return True

    return created


def reset_streak_freeze(user):
    """
    Resets streak freeze count to 1.
    Called weekly by Celery Beat.
    """
    from apps.gamification.models import UserGameProfile
    UserGameProfile.objects.filter(user=user).update(
        streak_freeze_count=1
    )