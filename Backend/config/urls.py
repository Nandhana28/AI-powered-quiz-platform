from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # django admin
    path('admin/', admin.site.urls),

    # api v1
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.quizzes.urls')),
    path('api/v1/', include('apps.attempts.urls')),
    path('api/v1/', include('apps.ai_generation.urls')),
    path('api/v1/', include('apps.gamification.urls')),

    # api docs
    path('api/schema/',  SpectacularAPIView.as_view(),        name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',   SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]