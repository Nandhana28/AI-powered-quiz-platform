from django.urls import path

from .views import (
    LeaderboardView,
    PersonalBestListView,
    TopicStatListView,
    UserBadgeListView,
    UserGameProfileView,
    WeeklyChallengeView,
)

urlpatterns = [
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("badges/", UserBadgeListView.as_view(), name="user-badges"),
    path("game-profile/", UserGameProfileView.as_view(), name="game-profile"),
    path("personal-bests/", PersonalBestListView.as_view(), name="personal-bests"),
    path("topic-stats/", TopicStatListView.as_view(), name="topic-stats"),
    path("weekly-challenge/", WeeklyChallengeView.as_view(), name="weekly-challenge"),
]
