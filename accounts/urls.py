from django.urls import path

from accounts import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("roles/", views.role_list, name="role_list"),
    path("roles/<int:pk>/edit/", views.role_edit, name="role_edit"),
    path("operation-logs/", views.operation_log_list, name="operation_logs"),
]
