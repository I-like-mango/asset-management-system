from django.urls import path

from assets import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("assets/", views.asset_list, name="asset_list"),
    path("assets/my/", views.my_assets, name="my_assets"),
    path("assets/create/", views.asset_create, name="asset_create"),
    path("assets/<int:pk>/", views.asset_detail, name="asset_detail"),
    path("assets/<int:pk>/edit/", views.asset_edit, name="asset_edit"),
    path("assets/<int:pk>/delete/", views.asset_delete, name="asset_delete"),
    path("assets/<int:pk>/qrcode/", views.asset_qrcode, name="asset_qrcode"),
    path("import-export/", views.import_export_view, name="import_export"),
    path("import-export/template/", views.import_template_download, name="import_template"),
    path("loans/apply/", views.loan_apply, name="loan_apply"),
    path("loans/mine/", views.my_loans, name="my_loans"),
    path("loans/<int:pk>/return/", views.loan_return_request, name="loan_return_request"),
    path("approvals/", views.approval_list, name="approval_list"),
    path("approvals/<int:pk>/<str:action>/", views.approval_action, name="approval_action"),
    path("approvals/return/<int:pk>/", views.return_confirm, name="return_confirm"),
    path("reports/", views.reports, name="reports"),
]
