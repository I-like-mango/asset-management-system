from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from audit.services import log_operation
from common.decorators import admin_required, permission_required
from notifications.models import EmailLog, Message
from notifications.services import email_service, message_service


@login_required
@permission_required("menu.messages")
def message_list(request):
    msg_type = request.GET.get("type", "")
    qs = Message.objects.filter(recipient=request.user)
    if msg_type:
        qs = qs.filter(msg_type=msg_type)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "notifications/message_list.html", {"page_obj": page, "msg_type": msg_type})


@login_required
@permission_required("menu.messages")
def message_detail(request, pk):
    msg = get_object_or_404(Message, pk=pk, recipient=request.user)
    message_service.mark_read(msg)
    return render(request, "notifications/message_detail.html", {"message": msg})


@login_required
def message_mark_read(request, pk):
    msg = get_object_or_404(Message, pk=pk, recipient=request.user)
    message_service.mark_read(msg)
    return redirect(request.META.get("HTTP_REFERER") or "message_list")


@login_required
def message_mark_all_read(request):
    message_service.mark_all_read(request.user)
    messages.success(request, "已全部标为已读")
    return redirect("message_list")


@login_required
def message_delete(request, pk):
    msg = get_object_or_404(Message, pk=pk, recipient=request.user)
    if request.method == "POST":
        msg.delete()
        messages.success(request, "已删除")
    return redirect("message_list")


@login_required
@admin_required
def email_log_list(request):
    qs = EmailLog.objects.all()
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "notifications/email_logs.html", {"page_obj": page})


@login_required
@admin_required
def email_retry(request, pk):
    log = get_object_or_404(EmailLog, pk=pk)
    email_service.send_email_log(log)
    log_operation(request, "email_retry", "notification", log.pk)
    messages.info(request, f"邮件状态：{log.status}")
    return redirect("email_log_list")
