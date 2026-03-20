import os
import django

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings.production'
)
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@quizapp.com')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpass123')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"Superuser created: {email}")
else:
    print(f"Superuser already exists: {email}")