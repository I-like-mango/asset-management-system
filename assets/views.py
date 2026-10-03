import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from assets.forms import ApprovalForm, AssetFilterForm, AssetForm, ExportForm, ImportForm, LoanApplyForm
from assets.models import Asset, AssetLoan, Attachment
from assets.services import asset_service, import_export_service, loan_service, stats_service
from assets.utils.filters import filter_assets
from audit.services import log_operation
from common.constants import AssetStatus, LoanStatus
from common.decorators import admin_required, handle_business_errors, is_admin, permission_required
from common.exceptions import BusinessError


@login_required
@permission_required("menu.dashboard")
def dashboard(request):
    user_scope = None if is_admin(request.user) else request.user
    stats = stats_service.dashboard_stats(for_user=user_scope)
    return render(request, "assets/dashboard.html", {"stats": stats, "stats_json": json.dumps(stats)})


@login_required
@permission_required("menu.assets")
def asset_list(request):
    if not is_admin(request.user):
        messages.error(request, "无权访问资产列表")
        return redirect("my_assets")
    qs = Asset.objects.filter(is_deleted=False).select_related("category", "current_holder")
    form = AssetFilterForm(request.GET or None)
    params = request.GET.copy() if request.GET else {}
    if form.is_valid():
        cd = form.cleaned_data
        params = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in cd.items() if v not in (None, "")}
        if cd.get("overdue"):
            params["overdue"] = "1"
    qs = filter_assets(qs, params)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "assets/asset_list.html",
        {"page_obj": page, "filter_form": form, "can_manage": user_has_perm(request, "btn.asset_create")},
    )


def user_has_perm(request, code):
    from accounts.services import user_has_permission

    return user_has_permission(request.user, code)


@login_required
@permission_required("menu.my_assets")
def my_assets(request):
    qs = Asset.objects.filter(is_deleted=False, current_holder=request.user).select_related("category")
    form = AssetFilterForm(request.GET or None)
    params = request.GET.copy() if request.GET else {}
    if form.is_valid():
        cd = form.cleaned_data
        params = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in cd.items() if v not in (None, "")}
    qs = filter_assets(qs, params, for_user=request.user)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "assets/my_assets.html", {"page_obj": page, "filter_form": form})


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    if not loan_service.user_can_view_asset(request.user, asset):
        messages.error(request, "无权查看该资产")
        return redirect("dashboard")
    logs = asset.status_logs.select_related("operator")[:20]
    loans = asset.loans.select_related("applicant")[:10]
    return render(
        request,
        "assets/asset_detail.html",
        {"asset": asset, "logs": logs, "loans": loans},
    )


@login_required
@permission_required("btn.asset_create")
@admin_required
@handle_business_errors
def asset_create(request):
    form = AssetForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        asset = asset_service.create_asset(data, request.user)
        _save_attachments(request, asset)
        log_operation(request, "create", "asset", asset.pk, str(asset))
        messages.success(request, "资产已创建")
        return redirect("asset_detail", pk=asset.pk)
    return render(request, "assets/asset_form.html", {"form": form, "title": "新增资产"})


@login_required
@permission_required("btn.asset_edit")
@admin_required
@handle_business_errors
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    form = AssetForm(request.POST or None, request.FILES or None, instance=asset)
    if request.method == "POST" and form.is_valid():
        asset_service.update_asset(asset, form.cleaned_data, request.user)
        _save_attachments(request, asset)
        log_operation(request, "update", "asset", asset.pk, str(asset))
        messages.success(request, "资产已更新")
        return redirect("asset_detail", pk=asset.pk)
    return render(request, "assets/asset_form.html", {"form": form, "title": "编辑资产", "asset": asset})


@login_required
@permission_required("btn.asset_delete")
@admin_required
@handle_business_errors
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    if request.method == "POST":
        asset_service.soft_delete_asset(asset, request.user)
        log_operation(request, "delete", "asset", asset.pk, str(asset))
        messages.success(request, "资产已删除")
        return redirect("asset_list")
    return render(request, "assets/asset_confirm_delete.html", {"asset": asset})


def _save_attachments(request, asset):
    files = request.FILES.getlist("attachments")
    for f in files:
        Attachment.objects.create(
            asset=asset,
            file=f,
            filename=f.name,
            uploaded_by=request.user,
        )


@login_required
@permission_required("menu.import_export")
@admin_required
def import_export_view(request):
    import_form = ImportForm(request.POST or None, request.FILES or None)
    export_form = ExportForm(request.POST or None)
    import_result = None
    if request.method == "POST" and request.POST.get("action") == "import":
        if import_form.is_valid():
            import_result = import_export_service.import_assets_from_file(
                import_form.cleaned_data["file"], request.user
            )
            log_operation(request, "import", "asset", detail=import_result)
            messages.info(request, f"成功导入 {import_result['success']} 条")
    if request.method == "POST" and request.POST.get("action") == "export":
        qs = Asset.objects.filter(is_deleted=False).select_related("category", "current_holder")
        form = AssetFilterForm(request.GET or None)
        params = {}
        if form.is_valid():
            cd = form.cleaned_data
            params = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in cd.items() if v}
        qs = filter_assets(qs, params)
        fields = request.POST.getlist("fields")
        return import_export_service.export_assets_queryset(qs, fields)
    return render(
        request,
        "assets/import_export.html",
        {"import_form": import_form, "export_form": export_form, "import_result": import_result},
    )


@login_required
def import_template_download(request):
    if not user_has_perm(request, "btn.asset_import"):
        messages.error(request, "无权下载模板")
        return redirect("dashboard")
    return import_export_service.build_import_template()


@login_required
@permission_required("menu.loan_apply")
@handle_business_errors
def loan_apply(request):
    form = LoanApplyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        loan = loan_service.apply_loan(
            request.user,
            form.cleaned_data["asset"].pk,
            form.cleaned_data["purpose"],
            form.cleaned_data["expected_return_at"],
        )
        log_operation(request, "apply", "loan", loan.pk, str(loan))
        messages.success(request, "领用申请已提交")
        return redirect("my_loans")
    return render(request, "assets/loan_apply.html", {"form": form})


@login_required
@permission_required("menu.my_loans")
def my_loans(request):
    qs = AssetLoan.objects.filter(applicant=request.user).select_related("asset")
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "assets/my_loans.html", {"page_obj": page})


@login_required
@handle_business_errors
def loan_return_request(request, pk):
    loan_service.request_return(request.user, pk)
    log_operation(request, "return_request", "loan", pk)
    messages.success(request, "归还申请已提交，等待管理员确认")
    return redirect("my_loans")


@login_required
@permission_required("menu.approval")
@admin_required
def approval_list(request):
    status = request.GET.get("status", LoanStatus.PENDING)
    qs = AssetLoan.objects.select_related("asset", "applicant").filter(status=status)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "assets/approval_list.html", {"page_obj": page, "current_status": status})


@login_required
@permission_required("btn.loan_approve")
@admin_required
@handle_business_errors
def approval_action(request, pk, action):
    loan = get_object_or_404(AssetLoan, pk=pk)
    form = ApprovalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        approved = action == "approve"
        loan_service.approve_loan(loan, request.user, approved, form.cleaned_data.get("comment", ""))
        log_operation(request, action, "loan", loan.pk, str(loan))
        messages.success(request, "审批已完成")
        return redirect("approval_list")
    return render(request, "assets/approval_form.html", {"loan": loan, "form": form, "action": action})


@login_required
@admin_required
@handle_business_errors
def return_confirm(request, pk):
    loan = get_object_or_404(AssetLoan, pk=pk)
    if request.method == "POST":
        loan_service.confirm_return(loan, request.user)
        log_operation(request, "return_confirm", "loan", loan.pk)
        messages.success(request, "归还已确认")
        return redirect("approval_list")
    return render(request, "assets/return_confirm.html", {"loan": loan})


@login_required
@permission_required("menu.reports")
def reports(request):
    scope = None if is_admin(request.user) else request.user
    stats = stats_service.dashboard_stats(for_user=scope)
    return render(request, "assets/dashboard.html", {"stats": stats, "stats_json": json.dumps(stats)})


@login_required
def asset_qrcode(request, pk):
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    if not loan_service.user_can_view_asset(request.user, asset):
        raise BusinessError("无权查看")
    if not asset.qr_code:
        asset_service.save_asset(asset, request.user, regenerate_qr=True)
    from django.http import FileResponse

    return FileResponse(asset.qr_code.open("rb"), content_type="image/png")
