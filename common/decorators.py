from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect

from common.constants import GROUP_ADMIN
from common.exceptions import BusinessError


def user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def is_admin(user) -> bool:
    return user.is_superuser or user_in_group(user, GROUP_ADMIN)


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "无权访问管理员功能。")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def permission_required(perm_code: str):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            from accounts.services import user_has_permission

            if not user_has_permission(request.user, perm_code):
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"ok": False, "message": "权限不足"}, status=403)
                return HttpResponseForbidden("权限不足")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def handle_business_errors(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except BusinessError as exc:
            messages.error(request, exc.message)
            referer = request.META.get("HTTP_REFERER")
            if referer:
                return redirect(referer)
            return redirect("dashboard")

    return _wrapped
