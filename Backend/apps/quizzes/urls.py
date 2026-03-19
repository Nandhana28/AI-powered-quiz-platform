from django.urls import path
from .views import (
    TopicListView,
    TopicDetailView,
    QuizListView,
    QuizDetailView,
    QuestionCreateView,
)

urlpatterns = [
    path('topics/',                          TopicListView.as_view(),    name='topic-list'),
    path('topics/<int:topic_id>/',           TopicDetailView.as_view(),  name='topic-detail'),
    path('quizzes/',                         QuizListView.as_view(),     name='quiz-list'),
    path('quizzes/<int:quiz_id>/',           QuizDetailView.as_view(),   name='quiz-detail'),
    path('quizzes/<int:quiz_id>/questions/', QuestionCreateView.as_view(), name='question-create'),
]