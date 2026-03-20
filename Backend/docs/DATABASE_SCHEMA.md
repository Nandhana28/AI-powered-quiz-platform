# Database Schema

## Tables

### users
Custom user model extending AbstractUser.
Login field: email (not username).
role: user | admin

### user_profiles
OneToOne with users.
Created automatically via signal on registration.
Supports soft delete.

### topics
Self-referencing hierarchy.
level 1 = domain (Computer Science, Maths)
level 2 = subject (Backend, Algebra)
level 3 = subtopic (Django, Calculus)
Quiz always linked to level 3.

### quizzes
Belongs to topic.
is_ai_generated flag.
Soft delete — never hard deleted.
is_published controls visibility.

### questions
Belongs to quiz.
explanation shown only after submission.
order field ensures consistent sequence.

### choices
4 per question.
is_correct never sent during active attempt.

### quiz_attempts
status: in_progress | submitted | expired | abandoned
expires_at copied from quiz at start time — locked in.
score, percentage, xp_earned calculated on submit.

### attempt_answers
unique_together: (attempt, question)
is_correct calculated server-side — never trusted from client.

### ai_generation_requests
Tracks full Gemini call lifecycle.
raw_response stored for re-parsing.
status: pending | processing | completed | failed

### audit_logs
Append-only. Never updated or deleted.
Tracks all significant actions.

## Key Constraints
- unique_together: (name, parent) on topics
- unique_together: (attempt, question) on attempt_answers
- Email unique on users
- Token unique on password_reset_tokens