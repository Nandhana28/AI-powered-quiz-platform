from django.urls import path
from .views import (
    GenerateQuizView,
    GenerationStatusView,
    GenerationHistoryView,
)

urlpatterns = [
    path('ai/generate/',               GenerateQuizView.as_view(),     name='ai-generate'),
    path('ai/status/<int:request_id>/', GenerationStatusView.as_view(), name='ai-status'),
    path('ai/history/',                GenerationHistoryView.as_view(), name='ai-history'),
]