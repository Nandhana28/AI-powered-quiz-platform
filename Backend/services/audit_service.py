def log_action(actor, action, resource_type, resource_id=None,
               description='', metadata=None, ip_address=None):
    from apps.analytics.models import AuditLog
    AuditLog.objects.create(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        metadata=metadata or {},
        ip_address=ip_address,
    )


def log_quiz_created(actor, quiz, ip_address=None):
    log_action(
        actor=actor,
        action='created',
        resource_type='Quiz',
        resource_id=quiz.id,
        description=f'Quiz created: {quiz.title}',
        ip_address=ip_address,
    )


def log_attempt_submitted(actor, attempt, ip_address=None):
    log_action(
        actor=actor,
        action='submitted',
        resource_type='QuizAttempt',
        resource_id=attempt.id,
        description=f'Attempt submitted: {attempt.quiz.title}',
        metadata={
            'score':      attempt.score,
            'percentage': attempt.percentage,
            'xp_earned':  attempt.xp_earned,
        },
        ip_address=ip_address,
    )


def log_user_login(user, status, ip_address=None):
    log_action(
        actor=user,
        action='login',
        resource_type='User',
        resource_id=user.id if user else None,
        description=f'Login {status}',
        ip_address=ip_address,
    )


def log_badge_earned(user, badge):
    log_action(
        actor=user,
        action='created',
        resource_type='UserBadge',
        resource_id=user.id,
        description=f'Badge earned: {badge}',
        metadata={'badge': badge},
    )