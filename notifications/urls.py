from django.urls import path

from notifications import views

urlpatterns = [
    path("", views.message_list, name="message_list"),
    path("<int:pk>/", views.message_detail, name="message_detail"),
    path("<int:pk>/read/", views.message_mark_read, name="message_mark_read"),
    path("read-all/", views.message_mark_all_read, name="message_mark_all_read"),
    path("<int:pk>/delete/", views.message_delete, name="message_delete"),
    path("admin/email-logs/", views.email_log_list, name="email_logs"),
    path("admin/email-logs/<int:pk>/retry/", views.email_retry, name="email_retry"),
]
