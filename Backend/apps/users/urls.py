from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    MeView,
    DashboardView,
    AdminUserListView,
    AdminUserDetailView,
    AdminDashboardView,
)

urlpatterns = [
    path('auth/register/',               RegisterView.as_view(),              name='register'),
    path('auth/login/',                  LoginView.as_view(),                 name='login'),
    path('auth/logout/',                 LogoutView.as_view(),                name='logout'),
    path('auth/password-reset/',         PasswordResetRequestView.as_view(),  name='password-reset-request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(),  name='password-reset-confirm'),
    path('auth/change-password/',        ChangePasswordView.as_view(),        name='change-password'),
    path('users/me/',                    MeView.as_view(),                    name='me'),
    path('users/dashboard/',             DashboardView.as_view(),             name='dashboard'),
    path('admin/users/',                 AdminUserListView.as_view(),         name='admin-users'),
    path('admin/users/<int:user_id>/',   AdminUserDetailView.as_view(),       name='admin-user-detail'),
    path('admin/dashboard/',             AdminDashboardView.as_view(),        name='admin-dashboard'),
]