# Design Decisions

## Architecture
- Layered: urls → views → serializers → services → models
- Views are thin — they only handle HTTP concerns
- Services contain all business logic
- Models define schema only

## Database
- PostgreSQL for ACID compliance and JSON field support
- Soft deletes on Quiz and Question — preserves attempt history
- Indexes on frequently queried fields (user+quiz, user+status)
- unique_together constraints enforced at DB level

## Authentication
- JWT via simplejwt — stateless, scalable
- Token blacklisting on logout
- Email as login field (not username)
- Login history tracked for security monitoring

## AI Integration
- Synchronous for now — Celery async in Phase 2
- raw_response stored on every request
- Deduplication before saving questions
- prompt_used stored for debugging

## API Design
- RESTful resource naming
- Consistent response envelope: {success, message, data}
- Versioned from day one: /api/v1/
- Pagination on all list endpoints
- Filtering via query params

## Security Decisions
- is_correct excluded from all serializers during attempt
- Ownership check on every attempt answer endpoint
- Admin role checked in view layer, not just URL permissions
- Password reset tokens are UUID — unguessable
- Token expiry: 15 minutes for reset, 60 minutes for access