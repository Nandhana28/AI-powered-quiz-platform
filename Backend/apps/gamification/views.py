from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.users.views import success_response, error_response
from services import analytics_service


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        topic_id   = request.query_params.get('topic')
        difficulty = request.query_params.get('difficulty')
        data = analytics_service.get_leaderboard(
            topic_id=topic_id,
            difficulty=difficulty,
        )
        return success_response(data=data)


class UserBadgeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.gamification.models import UserBadge
        badges = UserBadge.objects.filter(
            user=request.user
        ).select_related('badge').order_by('-earned_at')

        data = [
            {
                'name':        ub.badge.name,
                'description': ub.badge.description,
                'icon_key':    ub.badge.icon_key,
                'earned_at':   ub.earned_at,
            }
            for ub in badges
        ]
        return success_response(data=data)


class UserGameProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.gamification.models import UserGameProfile
        try:
            profile = UserGameProfile.objects.get(user=request.user)
            data = {
                'xp_total':            profile.xp_total,
                'level':               profile.level,
                'streak_easy':         profile.streak_easy,
                'streak_medium':       profile.streak_medium,
                'streak_hard':         profile.streak_hard,
                'streak_freeze_count': profile.streak_freeze_count,
                'last_active_date':    profile.last_active_date,
            }
            return success_response(data=data)
        except UserGameProfile.DoesNotExist:
            return error_response(
                message='Game profile not found',
                status_code=404
            )


class PersonalBestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.gamification.models import PersonalBest
        bests = PersonalBest.objects.filter(
            user=request.user
        ).select_related('topic').order_by('-best_score')

        data = [
            {
                'topic':      pb.topic.name,
                'topic_path': pb.topic.get_full_path(),
                'difficulty': pb.difficulty,
                'best_score': pb.best_score,
                'achieved_at': pb.achieved_at,
            }
            for pb in bests
        ]
        return success_response(data=data)


class TopicStatListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.gamification.models import UserTopicStat
        stats = UserTopicStat.objects.filter(
            user=request.user
        ).select_related('topic').order_by('-last_attempted_at')

        data = [
            {
                'topic':           s.topic.name,
                'topic_path':      s.topic.get_full_path(),
                'total_attempts':  s.total_attempts,
                'avg_score':       s.avg_score,
                'best_score':      s.best_score,
                'last_attempted_at': s.last_attempted_at,
            }
            for s in stats
        ]
        return success_response(data=data)