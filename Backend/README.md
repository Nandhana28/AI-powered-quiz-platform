# AI-Powered Quiz API — Backend

A production-ready REST API for an AI-powered quiz application with gamification, built with Django, PostgreSQL, and Google Gemini.

## Overview

This backend provides a complete quiz platform with:
- **User Management**: Registration, authentication, email verification, password reset
- **Quiz System**: Hierarchical topics, manual & AI-generated quizzes, soft deletes
- **Attempt Tracking**: Real-time answer submission, server-side validation, scoring
- **Gamification**: XP system, 5-tier levels, 7 badge types, streaks, personal bests
- **Analytics**: Topic statistics, percentile rankings, difficulty suggestions
- **AI Integration**: Google Gemini quiz generation with deduplication
- **Security**: JWT auth, role-based access, audit logging, rate limiting

## Tech Stack

- **Framework**: Django 6.0.3 + Django REST Framework 3.17.0
- **Database**: PostgreSQL 18 (ACID compliance, JSON fields)
- **Authentication**: JWT via simplejwt with token blacklisting
- **AI**: Google Gemini 2.0 Flash Lite
- **Documentation**: drf-spectacular (Swagger/ReDoc)
- **Testing**: pytest + Factory Boy
- **Code Quality**: Black, isort, pre-commit hooks

## Architecture

### Layered Design
```
URLs → Views (HTTP) → Serializers (Validation) → Services (Business Logic) → Models (Schema)
```

- **Views**: Thin HTTP handlers, permission checks, response formatting
- **Services**: Pure business logic, no HTTP concerns, reusable across endpoints
- **Models**: Schema definition only, soft deletes for audit trail
- **Serializers**: Input validation, output formatting, nested relationships

### Key Design Decisions

1. **Server-side Validation**: `is_correct` never sent to client, always calculated server-side
2. **Soft Deletes**: Quiz/Question deletions preserve attempt history
3. **Ownership Checks**: Every attempt endpoint validates user ownership
4. **Actual Question Count**: Uses `quiz.actual_question_count` property, not stored value
5. **Explicit Skipped Records**: Creates AttemptAnswer records for unanswered questions
6. **Rate Limiting**: 20/day anon, 100/day authenticated users
7. **Email Verification**: Required before account activation
8. **Token Expiry**: 15 min reset tokens, 60 min access tokens, 7 day refresh tokens

## Local Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 12+
- Git
- pip or uv (Python package manager)

### Installation

1. **Clone and navigate**
```bash
git clone <repo>
cd Backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings:
# - SECRET_KEY (generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
# - GEMINI_API_KEY (from Google AI Studio)
# - FRONTEND_URL (http://localhost:3000 for dev)
```

5. **Setup database**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_topics  # Optional: populate topic hierarchy
```

6. **Run development server**
```bash
python manage.py runserver
```

Server runs at `http://localhost:8000`
API Docs at `http://localhost:8000/api/docs/`

## Environment Variables

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=quizapp_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Google Gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.0-flash-lite

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@quizapp.com

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5500
FRONTEND_URL=http://localhost:3000
```

## API Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /register/` — Create account
- `POST /login/` — Get JWT tokens
- `POST /logout/` — Blacklist refresh token
- `POST /verify-email/` — Verify email with token
- `POST /resend-verify/` — Resend verification email
- `POST /password-reset/` — Request password reset
- `POST /password-reset/confirm/` — Reset password with token
- `POST /change-password/` — Change password (authenticated)

### Users (`/api/v1/users/`)
- `GET /me/` — Current user profile
- `PATCH /me/` — Update profile
- `GET /dashboard/` — User dashboard with stats
- `GET /admin/users/` — List all users (admin)
- `GET /admin/users/<id>/` — User details (admin)
- `PATCH /admin/users/<id>/` — Update user (admin)
- `GET /admin/dashboard/` — Admin dashboard

### Topics (`/api/v1/topics/`)
- `GET /` — List topics (with filtering by level/parent)
- `GET /<id>/` — Topic details with hierarchy

### Quizzes (`/api/v1/quizzes/`)
- `GET /` — List published quizzes (with filtering)
- `POST /` — Create quiz (admin)
- `GET /<id>/` — Quiz details with questions
- `PATCH /<id>/` — Update quiz (admin)
- `DELETE /<id>/` — Soft delete quiz (admin)
- `POST /<id>/questions/` — Add question to quiz (admin)

### Attempts (`/api/v1/attempts/`)
- `POST /start/` — Start new attempt
- `POST /<id>/answer/` — Submit answer to question
- `POST /<id>/submit/` — Submit completed attempt
- `GET /<id>/results/` — Get attempt results (after submission)
- `GET /history/` — Get user's attempt history

### AI Generation (`/api/v1/ai/`)
- `POST /generate/` — Generate quiz with AI (rate limited 10/day)
- `GET /status/<id>/` — Check generation status
- `GET /history/` — Generation request history

### Gamification (`/api/v1/`)
- `GET /leaderboard/` — Global XP leaderboard
- `GET /badges/` — User's earned badges
- `GET /game-profile/` — User's game profile (XP, level, streaks)
- `GET /personal-bests/` — User's personal best scores
- `GET /topic-stats/` — User's topic statistics
- `GET /weekly-challenge/` — Current weekly challenge quiz

## Database Schema

### Core Models

**User** (Custom AbstractUser)
- Email-based login (not username)
- Role: user | admin
- Soft-deletable profile

**Topic** (Hierarchical)
- Level 1: Domain (Computer Science, Mathematics)
- Level 2: Subject (Backend, Algebra)
- Level 3: Subtopic (Django, Calculus)
- Self-referencing parent relationship

**Quiz**
- Belongs to Topic (level 3)
- Difficulty: easy | medium | hard
- Soft-deletable with audit trail
- AI-generated flag
- Weekly challenge support

**Question**
- Belongs to Quiz
- 4 choices per question (enforced)
- 1 correct choice per question (enforced)
- Explanation shown only after submission
- Soft-deletable

**QuizAttempt**
- User + Quiz relationship
- Status: in_progress | submitted | expired | abandoned
- Scoring: score, percentage, XP earned
- Time tracking: started_at, submitted_at, time_taken_seconds
- Late submission detection

**AttemptAnswer**
- Unique per (attempt, question)
- Server-side correctness validation
- Marks awarded calculation
- Explicit records for skipped questions

**UserGameProfile**
- XP total and level (5 tiers)
- Streaks per difficulty with freeze mechanic
- Last active date tracking

**Badge & UserBadge**
- 7 badge types (first quiz, streaks, perfect scores, etc.)
- Unique per user
- Earned timestamp

**PersonalBest**
- Best score per (user, topic, difficulty)
- Unique constraint enforced

**UserTopicStat**
- Aggregate stats per (user, topic)
- Total attempts, correct count, average score
- Best score tracking

**AuditLog** (Append-only)
- Tracks all significant actions
- Never updated or deleted
- IP address and metadata

## Key Features

### Quiz Management
- Hierarchical topic system with 3 levels
- Manual quiz creation with question builder
- AI-generated quizzes via Google Gemini
- Soft deletes preserve attempt history
- Weekly challenges with bonus XP
- Time limits and pass percentages
- Availability windows (available_from, expires_at)

### Attempt System
- Real-time answer submission
- Server-side correctness validation (never trust client)
- Automatic scoring with XP calculation
- Time tracking and late submission detection
- Explicit skipped question records
- Ownership validation on all endpoints

### Gamification
- **XP System**: Base XP = percentage, multiplied by difficulty (easy=1x, medium=1.5x, hard=2x)
- **Levels**: Novice (0) → Apprentice (500) → Scholar (1500) → Expert (3500) → Master (7000)
- **Streaks**: Per difficulty, with 1 freeze per week
- **Badges**: 7 types (first quiz, 5-day streak, perfect hard, 5 topics, comeback, speed demon, 100 quizzes)
- **Personal Bests**: Tracked per topic/difficulty
- **Topic Stats**: Aggregate performance per topic

### AI Generation
- Google Gemini integration for quiz creation
- Automatic deduplication of questions
- Full response logging for debugging
- Rate limiting: 10 requests/day per user
- Status tracking: pending → processing → completed/failed
- Retry mechanism with max 3 attempts

### Security
- JWT authentication with token blacklisting
- Email verification required
- Password reset with time-limited tokens (15 min)
- Role-based access control (user/admin)
- Ownership validation on all user resources
- Login history tracking
- Rate throttling (20/day anon, 100/day auth)
- CORS configured
- HSTS, XSS protection in production

### Analytics
- User topic statistics (attempts, accuracy, best scores)
- Percentile rankings per quiz
- Difficulty suggestions based on performance
- Admin dashboard with system metrics
- Audit logs for compliance

## Testing

### Run Tests
```bash
pytest                          # All tests
pytest tests/attempts/          # Specific app
pytest tests/attempts/test_scoring.py  # Specific file
pytest -v                       # Verbose
pytest --cov                    # Coverage report
```

### Test Fixtures (conftest.py)
- `api_client` — Unauthenticated API client
- `test_user` — Regular user
- `admin_user` — Admin user
- `auth_client` — Authenticated client
- `admin_client` — Admin authenticated client

### Test Factories (factories.py)
- UserFactory
- QuizFactory
- QuestionFactory
- ChoiceFactory
- QuizAttemptFactory
- AttemptAnswerFactory

## Deployment

### Production Checklist
```bash
# 1. Set DEBUG=False in production settings
# 2. Generate strong SECRET_KEY
# 3. Configure ALLOWED_HOSTS
# 4. Set up PostgreSQL (not SQLite)
# 5. Configure email backend (Gmail, SendGrid, etc.)
# 6. Set SECURE_HSTS_SECONDS, SECURE_SSL_REDIRECT
# 7. Collect static files: python manage.py collectstatic
# 8. Run migrations: python manage.py migrate
# 9. Create superuser: python manage.py createsuperuser
# 10. Use gunicorn/uWSGI as app server
# 11. Use nginx as reverse proxy
# 12. Enable HTTPS with SSL certificate
```

### Railway Deployment
```bash
# 1. Push to GitHub
# 2. Connect repo to Railway
# 3. Add PostgreSQL plugin
# 4. Set environment variables in Railway dashboard
# 5. Deploy automatically on push
```

### Docker (Optional)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Common Tasks

### Create Superuser
```bash
python manage.py createsuperuser
```

### Seed Topics
```bash
python manage.py seed_topics
```

### View Badges
```bash
python manage.py see_badges
```

### Create Password Reset Token
```bash
python manage.py shell
from apps.users.models import User
from services.auth_service import generate_password_reset_token
token = generate_password_reset_token('user@example.com')
print(token)
```

### Check Database
```bash
python manage.py dbshell
```

## Troubleshooting

### Migration Errors
```bash
# Reset migrations (dev only!)
python manage.py migrate apps.users zero
python manage.py migrate

# Or create new migration
python manage.py makemigrations
python manage.py migrate
```

### Email Not Sending
- Check EMAIL_BACKEND in settings
- For Gmail: Use app-specific password, enable "Less secure apps"
- For console backend: Check Django logs

### Gemini API Errors
- Verify GEMINI_API_KEY is set
- Check API quota in Google Cloud Console
- Ensure model name is correct (gemini-2.0-flash-lite)

### Database Connection
```bash
# Test connection
python manage.py dbshell

# Check settings
python manage.py shell
from django.conf import settings
print(settings.DATABASES)
```

### JWT Token Issues
- Token expired: Use refresh token to get new access token
- Invalid token: Check Authorization header format: `Bearer <token>`
- Blacklisted token: User logged out, need to login again

## Performance Optimization

### Database Queries
- Use `select_related()` for ForeignKey relationships
- Use `prefetch_related()` for reverse relationships
- Add indexes on frequently queried fields (already done)
- Use `only()` and `defer()` to limit fields

### Caching (Future)
- Cache topic hierarchy
- Cache leaderboard (update hourly)
- Cache user game profile

### Async Tasks (Phase 2)
- Move AI generation to Celery
- Async email sending
- Background badge checking

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes following code style (Black, isort)
3. Run tests: `pytest`
4. Commit: `git commit -m "feat: description"`
5. Push: `git push origin feature/name`
6. Create Pull Request

## Code Style

- **Formatter**: Black (line length 88)
- **Import Sorter**: isort (Black profile)
- **Linter**: Pre-commit hooks
- **Type Hints**: Recommended for new code

```bash
# Format code
black .
isort .

# Run pre-commit
pre-commit run --all-files
```

## License

MIT License — See LICENSE file

## Support

For issues, questions, or suggestions:
1. Check existing GitHub issues
2. Create new issue with details
3. Contact: support@quizapp.com