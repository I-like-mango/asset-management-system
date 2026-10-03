from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField("部门名称", max_length=100)
    code = models.CharField("部门编码", max_length=50, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级部门",
    )
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = verbose_name
        ordering = ["code"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="用户",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        verbose_name="部门",
    )
    employee_no = models.CharField("工号", max_length=50, blank=True)
    phone = models.CharField("手机号", max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "用户扩展信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.get_username()


class GroupPermission(models.Model):
    """角色（Django Group）与菜单/按钮权限绑定。"""

    group = models.ForeignKey(
        "auth.Group",
        on_delete=models.CASCADE,
        related_name="custom_permissions",
        verbose_name="角色",
    )
    permission_code = models.CharField("权限码", max_length=64, db_index=True)

    class Meta:
        verbose_name = "角色权限"
        verbose_name_plural = verbose_name
        unique_together = ("group", "permission_code")

    def __str__(self):
        return f"{self.group.name}:{self.permission_code}"


class MessageTemplate(models.Model):
    """消息/邮件模板（加分项）。"""

    code = models.CharField("模板编码", max_length=50, unique=True)
    name = models.CharField("名称", max_length=100)
    title_template = models.CharField("标题模板", max_length=200)
    body_template = models.TextField("正文模板")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "消息模板"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
