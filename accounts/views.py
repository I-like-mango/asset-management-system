from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import CustomPasswordChangeForm, LoginForm, ProfileForm, RolePermissionForm, UserForm
from accounts.models import Department, UserProfile
from accounts.services import get_or_create_profile, sync_group_permissions, user_has_permission
from audit.models import OperationLog
from audit.services import log_operation
from common.constants import GROUP_ADMIN, GROUP_USER, PERMISSION_CODES
from common.decorators import admin_required, handle_business_errors, permission_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    profile = get_or_create_profile(request.user)
    pwd_form = CustomPasswordChangeForm(request.user, request.POST or None)
    profile_form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile" and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "个人信息已更新")
            return redirect("profile")
        if action == "password" and pwd_form.is_valid():
            pwd_form.save()
            update_session_auth_hash(request, pwd_form.user)
            messages.success(request, "密码已修改")
            return redirect("profile")
    from assets.services.stats_service import dashboard_stats

    stats = dashboard_stats(for_user=request.user)
    return render(
        request,
        "accounts/profile.html",
        {"profile_form": profile_form, "pwd_form": pwd_form, "stats": stats},
    )


@admin_required
@permission_required("menu.users")
def user_list(request):
    dept = request.GET.get("department")
    qs = User.objects.select_related("profile__department").order_by("-date_joined")
    if dept:
        qs = qs.filter(profile__department_id=dept)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/user_list.html",
        {
            "page_obj": page,
            "departments": Department.objects.filter(is_active=True),
            "selected_department": dept or "",
        },
    )


@admin_required
@permission_required("menu.users")
@handle_business_errors
def user_create(request):
    form = UserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get("password") or "User@123456"
        user.set_password(password)
        user.save()
        group = form.cleaned_data["groups"]
        user.groups.set([group])
        profile = get_or_create_profile(user)
        profile.department = form.cleaned_data.get("department")
        profile.employee_no = form.cleaned_data.get("employee_no", "")
        profile.phone = form.cleaned_data.get("phone", "")
        profile.save()
        log_operation(request, "create", "user", user.pk, user.username)
        messages.success(request, "用户已创建")
        return redirect("user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "新增用户"})


@admin_required
@permission_required("menu.users")
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_or_create_profile(user)
    initial = {
        "groups": user.groups.first(),
        "department": profile.department,
        "employee_no": profile.employee_no,
        "phone": profile.phone,
    }
    form = UserForm(request.POST or None, instance=user, initial=initial)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        pwd = form.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
            user.save()
        user.groups.set([form.cleaned_data["groups"]])
        profile.department = form.cleaned_data.get("department")
        profile.employee_no = form.cleaned_data.get("employee_no", "")
        profile.phone = form.cleaned_data.get("phone", "")
        profile.save()
        log_operation(request, "update", "user", user.pk, user.username)
        messages.success(request, "用户已更新")
        return redirect("user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "编辑用户", "edit_user": user})


@admin_required
@permission_required("menu.roles")
def role_list(request):
    groups = Group.objects.filter(name__in=[GROUP_ADMIN, GROUP_USER])
    groups_data = []
    for g in groups:
        cnt = g.custom_permissions.count()
        groups_data.append({"group": g, "perm_count": cnt})
    return render(
        request,
        "accounts/role_list.html",
        {"groups_data": groups_data, "permission_labels": PERMISSION_CODES},
    )


@admin_required
@permission_required("menu.roles")
def role_edit(request, pk):
    group = get_object_or_404(Group, pk=pk, name__in=[GROUP_ADMIN, GROUP_USER])
    initial = {"permissions": list(group.custom_permissions.values_list("permission_code", flat=True))}
    form = RolePermissionForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        sync_group_permissions(group, form.cleaned_data.get("permissions", []))
        log_operation(request, "update", "role", group.pk, group.name)
        messages.success(request, "角色权限已更新")
        return redirect("role_list")
    return render(request, "accounts/role_form.html", {"form": form, "group": group})


@admin_required
def operation_log_list(request):
    qs = OperationLog.objects.select_related("user").all()
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/operation_logs.html", {"page_obj": page})
