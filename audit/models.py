from django.conf import settings
from django.db import models


class OperationLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="operation_logs",
    )
    action = models.CharField("操作", max_length=50, db_index=True)
    module = models.CharField("模块", max_length=50, db_index=True)
    object_id = models.CharField("对象ID", max_length=64, blank=True)
    object_repr = models.CharField("对象描述", max_length=255, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.object_repr}"
