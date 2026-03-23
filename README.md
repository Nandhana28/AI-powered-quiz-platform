# AI-Powered Quiz Platform

A full-stack web application for creating, taking, and sharing AI-generated quizzes with gamification features. Learn interactively with personalized difficulty suggestions and compete on global leaderboards.

##  Project Overview

**AI-Powered Quiz Platform** is a modern learning application that combines:
- **AI-Generated Content**: Automatically create quizzes using Google Gemini
- **Gamification**: Earn XP, unlock badges, climb levels, maintain streaks
- **Adaptive Learning**: Get difficulty suggestions based on your performance
- **Social Features**: Compete on leaderboards, track personal bests
- **Analytics**: Detailed performance insights per topic and difficulty

### Key Statistics
- **7 Badge Types**: First quiz, streaks, perfect scores, polymath, comeback, speed demon, century
- **5 Skill Levels**: Novice → Apprentice → Scholar → Expert → Master
- **3 Difficulty Tiers**: Easy, Medium, Hard (with XP multipliers)
- **Hierarchical Topics**: 3-level taxonomy (Domain → Subject → Subtopic)
- **Real-time Scoring**: Instant feedback with server-side validation

##  Architecture

### Full-Stack Structure
```
AI-Powered Quiz Platform
├── Backend (Django REST API)
│   ├── User Management & Auth
│   ├── Quiz System
│   ├── Attempt Tracking
│   ├── Gamification Engine
│   ├── AI Integration (Gemini)
│   └── Analytics & Audit
│
└── Frontend (Coming Soon)
    ├── User Interface
    ├── Quiz Player
    ├── Dashboard
    ├── Leaderboards
    └── Profile Management
```

### Technology Stack

#### Backend
- **Framework**: Django 6.0.3 + Django REST Framework 3.17.0
- **Database**: PostgreSQL 18 (ACID, JSON support)
- **Authentication**: JWT (simplejwt) with token blacklisting
- **AI**: Google Gemini 2.0 Flash Lite
- **Documentation**: drf-spectacular (Swagger/ReDoc)
- **Testing**: pytest + Factory Boy
- **Code Quality**: Black, isort, pre-commit

#### Frontend (Planned)
- **Framework**: React 18+ or Vue 3+
- **State Management**: Redux/Pinia
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library

#### DevOps
- **Deployment**: Railway, Heroku, or Docker
- **Database**: PostgreSQL (managed)
- **Static Files**: WhiteNoise
- **Monitoring**: Sentry (optional)

##  Quick Start

### Backend Setup

1. **Clone repository**
```bash
git clone <repo>
cd Backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Setup database**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_topics
```

6. **Run server**
```bash
python manage.py runserver
```

**API available at**: `http://localhost:8000`
**Docs at**: `http://localhost:8000/api/docs/`

### Frontend Setup (Coming Soon)
```bash
cd Frontend
npm install
npm run dev
```

##  Core Features

### 1. User Management
- Email-based registration with verification
- JWT authentication with refresh tokens
- Password reset with time-limited tokens
- User profiles with customization
- Role-based access (user/admin)
- Login history tracking

### 2. Quiz System
- **Hierarchical Topics**: 3-level taxonomy for organization
- **Manual Quizzes**: Admin-created quizzes with custom questions
- **AI-Generated Quizzes**: Automatic quiz creation via Gemini
- **Question Types**: Multiple choice (4 options, 1 correct)
- **Soft Deletes**: Preserve attempt history when deleting
- **Weekly Challenges**: Special quizzes with bonus XP
- **Availability Windows**: Schedule quiz availability

### 3. Quiz Attempts
- **Real-time Submission**: Answer questions one at a time
- **Server-side Validation**: Correctness calculated server-side
- **Time Tracking**: Monitor time spent per attempt
- **Late Submission Detection**: Track submissions after time limit
- **Automatic Scoring**: Instant score calculation with XP
- **Detailed Results**: View answers, explanations, and performance

### 4. Gamification System

#### XP & Levels
- **XP Calculation**: Base XP = percentage score
- **Difficulty Multipliers**: Easy (1x) → Medium (1.5x) → Hard (2x)
- **5 Skill Levels**:
  - Novice: 0 XP
  - Apprentice: 500 XP
  - Scholar: 1500 XP
  - Expert: 3500 XP
  - Master: 7000 XP

#### Streaks
- **Per-Difficulty Tracking**: Separate streaks for each difficulty
- **Freeze Mechanic**: 1 free miss per week
- **Consecutive Days**: Maintain streaks by attempting daily
- **Reset on Gap**: Streak resets if you miss a day (unless frozen)

#### Badges (7 Types)
1. **First Quiz**: Complete your first quiz
2. **5-Day Streak**: Maintain 5-day streak on any difficulty
3. **Perfect Hard**: Score 100% on a hard quiz
4. **Polymath**: Attempt quizzes in 5 different topics
5. **Comeback**: Score 70%+ after 3 consecutive failures
6. **Speed Demon**: Complete quiz in half the time limit
7. **Century**: Complete 100 quizzes

#### Personal Bests
- Track best score per (topic, difficulty)
- Automatic updates on new high scores
- Historical achievement tracking

#### Topic Statistics
- Attempts per topic
- Average score per topic
- Best score per topic
- Last attempted date

### 5. AI Integration
- **Gemini-Powered Generation**: Create quizzes automatically
- **Deduplication**: Prevent duplicate questions
- **Rate Limiting**: 10 requests/day per user
- **Status Tracking**: Monitor generation progress
- **Error Handling**: Retry mechanism with logging
- **Full Logging**: Store prompts and responses for debugging

### 6. Analytics & Insights
- **Percentile Rankings**: See how you rank on each quiz
- **Difficulty Suggestions**: Get recommendations based on performance
- **Topic Performance**: Detailed stats per topic
- **Leaderboards**: Global XP rankings
- **Admin Dashboard**: System-wide metrics

### 7. Security
- **JWT Authentication**: Stateless, scalable auth
- **Token Blacklisting**: Logout invalidates tokens
- **Email Verification**: Required before account activation
- **Password Reset**: Secure token-based reset
- **Ownership Validation**: Users can only access their data
- **Rate Limiting**: Prevent abuse (20/day anon, 100/day auth)
- **CORS Configuration**: Secure cross-origin requests
- **Audit Logging**: Track all significant actions
- **HTTPS Ready**: Production security headers

##  API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Authentication
All endpoints (except auth) require JWT token:
```
Authorization: Bearer <access_token>
```

### Response Format
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { /* response data */ }
}
```

### Key Endpoints

#### Authentication
- `POST /auth/register/` — Create account
- `POST /auth/login/` — Get tokens
- `POST /auth/logout/` — Logout
- `POST /auth/verify-email/` — Verify email
- `POST /auth/password-reset/` — Request reset
- `POST /auth/password-reset/confirm/` — Confirm reset

#### Quizzes
- `GET /quizzes/` — List quizzes
- `GET /quizzes/<id>/` — Quiz details
- `POST /quizzes/` — Create quiz (admin)
- `PATCH /quizzes/<id>/` — Update quiz (admin)
- `DELETE /quizzes/<id>/` — Delete quiz (admin)

#### Attempts
- `POST /attempts/start/` — Start attempt
- `POST /attempts/<id>/answer/` — Submit answer
- `POST /attempts/<id>/submit/` — Submit attempt
- `GET /attempts/<id>/results/` — View results
- `GET /attempts/history/` — Attempt history

#### Gamification
- `GET /leaderboard/` — Global leaderboard
- `GET /badges/` — User's badges
- `GET /game-profile/` — Game profile
- `GET /personal-bests/` — Personal bests
- `GET /topic-stats/` — Topic statistics
- `GET /weekly-challenge/` — Weekly challenge

#### AI Generation
- `POST /ai/generate/` — Generate quiz
- `GET /ai/status/<id>/` — Generation status
- `GET /ai/history/` — Generation history

**Full API docs**: `http://localhost:8000/api/docs/`

##  Database Schema

### Core Tables
- **users** — User accounts with roles
- **user_profiles** — User profile information
- **topics** — Hierarchical topic taxonomy
- **quizzes** — Quiz definitions
- **questions** — Quiz questions
- **choices** — Multiple choice options
- **quiz_attempts** — User attempt records
- **attempt_answers** — Individual answers
- **user_game_profiles** — Gamification data
- **badges** — Badge definitions
- **user_badges** — Earned badges
- **personal_bests** — Best scores per topic/difficulty
- **user_topic_stats** — Aggregate topic statistics
- **audit_logs** — Append-only action log

### Key Constraints
- Email unique on users
- (name, parent) unique on topics
- (attempt, question) unique on attempt_answers
- (user, badge) unique on user_badges
- (user, topic, difficulty) unique on personal_bests

##  Testing

### Run Tests
```bash
cd Backend
pytest                    # All tests
pytest tests/attempts/    # Specific app
pytest -v                 # Verbose
pytest --cov              # Coverage
```

### Test Coverage
- User authentication and authorization
- Quiz creation and management
- Attempt submission and scoring
- Gamification logic (XP, badges, streaks)
- AI generation and deduplication
- Analytics calculations

##  Deployment

### Environment Variables
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=quizapp_db
DB_USER=postgres
DB_PASSWORD=secure-password
DB_HOST=db.railway.app
DB_PORT=5432

# Gemini
GEMINI_API_KEY=your-api-key

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password

# Frontend
FRONTEND_URL=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Railway Deployment
1. Push code to GitHub
2. Connect repo to Railway
3. Add PostgreSQL plugin
4. Set environment variables
5. Deploy automatically

### Docker Deployment
```bash
docker build -t quiz-api .
docker run -p 8000:8000 quiz-api
```

##  Roadmap

### Phase 1 (Current) 
- [x] Backend API complete
- [x] User authentication
- [x] Quiz system
- [x] Attempt tracking
- [x] Gamification engine
- [x] AI integration
- [x] Analytics

### Phase 2 (Next)
- [ ] Frontend UI (React/Vue)
- [ ] Async task queue (Celery)
- [ ] Real-time notifications (WebSocket)
- [ ] Quiz sharing and collaboration
- [ ] Advanced analytics dashboard

### Phase 3 (Future)
- [ ] Mobile app (React Native)
- [ ] Offline mode
- [ ] Video explanations
- [ ] Community features
- [ ] Marketplace for quizzes

##  Contributing

### Setup Development Environment
```bash
git clone <repo>
cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

### Code Style
```bash
black .
isort .
pre-commit run --all-files
```

### Create Feature Branch
```bash
git checkout -b feature/your-feature
git commit -m "feat: description"
git push origin feature/your-feature
```

### Pull Request Process
1. Update README if needed
2. Add tests for new features
3. Ensure all tests pass
4. Request review

##  Documentation

- **Backend README**: `Backend/README.md` — Detailed backend documentation
- **API Docs**: `http://localhost:8000/api/docs/` — Interactive Swagger UI
- **Database Schema**: `Backend/docs/DATABASE_SCHEMA.md`
- **Design Decisions**: `Backend/docs/DESIGN_DECISIONS.md`

##  Troubleshooting

### Backend Issues
- **Migration errors**: `python manage.py migrate --fake-initial`
- **Email not sending**: Check EMAIL_BACKEND in settings
- **Gemini API errors**: Verify API key and quota
- **Database connection**: Check DATABASE settings

### Common Errors
- `ModuleNotFoundError`: Install requirements: `pip install -r requirements.txt`
- `OperationalError`: Run migrations: `python manage.py migrate`
- `CORS error`: Check CORS_ALLOWED_ORIGINS in settings


## Acknowledgments

- Django & Django REST Framework community
- Google Gemini API
- PostgreSQL
- All open-source contributors
