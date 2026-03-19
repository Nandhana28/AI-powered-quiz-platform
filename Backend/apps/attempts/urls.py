from django.urls import path
from .views import (
    StartAttemptView,
    AnswerView,
    SubmitAttemptView,
    AttemptResultView,
    AttemptHistoryView,
)

urlpatterns = [
    path('attempts/start/',                  StartAttemptView.as_view(),  name='attempt-start'),
    path('attempts/<int:attempt_id>/answer/', AnswerView.as_view(),        name='attempt-answer'),
    path('attempts/<int:attempt_id>/submit/', SubmitAttemptView.as_view(), name='attempt-submit'),
    path('attempts/<int:attempt_id>/results/',AttemptResultView.as_view(), name='attempt-results'),
    path('attempts/history/',                AttemptHistoryView.as_view(), name='attempt-history'),
]