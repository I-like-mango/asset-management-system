from django.conf import settings
from django.db import models

from common.constants import MessageType


class Message(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inbox_messages",
        verbose_name="接收人",
    )
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    msg_type = models.CharField(
        "类型",
        max_length=20,
        choices=MessageType.CHOICES,
        default=MessageType.SYSTEM,
        db_index=True,
    )
    is_read = models.BooleanField("已读", default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    related_key = models.CharField("关联键", max_length=128, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "站内信"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class EmailLog(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "待发送"),
        (STATUS_SENT, "已发送"),
        (STATUS_FAILED, "失败"),
    )

    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    dedup_key = models.CharField(max_length=128, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "邮件日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]


class ReminderLog(models.Model):
    """到期提醒去重记录。"""

    asset = models.ForeignKey("assets.Asset", on_delete=models.CASCADE, related_name="reminder_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reminder_kind = models.CharField(max_length=32)
    remind_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "提醒记录"
        verbose_name_plural = verbose_name
        unique_together = ("asset", "user", "reminder_kind", "remind_date")
