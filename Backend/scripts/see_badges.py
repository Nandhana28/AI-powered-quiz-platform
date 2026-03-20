import os
import django

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings.development'
)
django.setup()

from apps.gamification.models import Badge

BADGES = [
    {
        'name':           'First Blood',
        'description':    'Complete your first quiz',
        'icon_key':       'first_blood',
        'condition_type': 'first_quiz',
    },
    {
        'name':           'On Fire',
        'description':    'Maintain a 5 day streak on any difficulty',
        'icon_key':       'on_fire',
        'condition_type': 'streak_5',
    },
    {
        'name':           'Perfectionist',
        'description':    'Score 100% on a Hard difficulty quiz',
        'icon_key':       'perfectionist',
        'condition_type': 'perfect_hard',
    },
    {
        'name':           'Polymath',
        'description':    'Attempt quizzes in 5 different topics',
        'icon_key':       'polymath',
        'condition_type': 'five_topics',
    },
    {
        'name':           'Comeback Kid',
        'description':    'Score above 70% after 3 consecutive failures',
        'icon_key':       'comeback',
        'condition_type': 'comeback',
    },
    {
        'name':           'Speed Demon',
        'description':    'Finish a quiz in under half the time limit',
        'icon_key':       'speed_demon',
        'condition_type': 'speed_demon',
    },
    {
        'name':           'Century',
        'description':    'Complete 100 quizzes',
        'icon_key':       'century',
        'condition_type': 'century',
    },
]

created = 0
for badge_data in BADGES:
    _, new = Badge.objects.get_or_create(
        name=badge_data['name'],
        defaults=badge_data
    )
    if new:
        created += 1

print(f"Done — {created} badges created.")