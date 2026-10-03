from django.conf import settings
from django.db import models
from django.utils import timezone

from common.constants import AssetStatus, LoanStatus


class AssetCategory(models.Model):
    name = models.CharField("分类名称", max_length=100)
    code = models.CharField("分类编码", max_length=50, unique=True)
    warning_threshold = models.PositiveIntegerField(
        "库存预警阈值",
        default=5,
        help_text="在库数量低于等于该值时预警",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "资产分类"
        verbose_name_plural = verbose_name
        ordering = ["code"]

    def __str__(self):
        return self.name

    @property
    def in_stock_count(self):
        return self.assets.filter(is_deleted=False, status=AssetStatus.IN_STOCK).count()


class Asset(models.Model):
    asset_no = models.CharField("资产编号", max_length=64, unique=True, db_index=True)
    name = models.CharField("资产名称", max_length=200)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name="assets",
        verbose_name="分类",
    )
    brand = models.CharField("品牌", max_length=100, blank=True)
    model = models.CharField("型号", max_length=100, blank=True)
    serial_no = models.CharField("序列号", max_length=100, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=AssetStatus.CHOICES,
        default=AssetStatus.IN_STOCK,
        db_index=True,
    )
    location = models.CharField("存放位置", max_length=200, blank=True)
    purchase_date = models.DateField("采购日期", null=True, blank=True)
    warranty_until = models.DateField("保修截止", null=True, blank=True)
    price = models.DecimalField("采购价格", max_digits=12, decimal_places=2, null=True, blank=True)
    current_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="held_assets",
        verbose_name="当前领用人",
    )
    loaned_at = models.DateTimeField("领用时间", null=True, blank=True)
    due_at = models.DateTimeField("到期时间", null=True, blank=True, db_index=True)
    remark = models.TextField("备注", blank=True)
    qr_code = models.ImageField("二维码", upload_to="qrcodes/", blank=True, null=True)
    is_deleted = models.BooleanField("已删除", default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assets",
        verbose_name="创建人",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "资产"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.asset_no} - {self.name}"

    @property
    def is_overdue(self):
        if self.status != AssetStatus.LOANED or not self.due_at:
            return False
        return timezone.now() > self.due_at

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


class AssetLoan(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="loans", verbose_name="资产")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loan_applications",
        verbose_name="申请人",
    )
    purpose = models.TextField("用途说明")
    expected_return_at = models.DateTimeField("预计归还时间")
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.CHOICES,
        default=LoanStatus.PENDING,
        db_index=True,
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    actual_return_at = models.DateTimeField(null=True, blank=True)
    admin_remark = models.TextField("审批意见", blank=True)

    class Meta:
        verbose_name = "领用申请"
        verbose_name_plural = verbose_name
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.asset.asset_no} - {self.applicant.username}"


class ApprovalRecord(models.Model):
    loan = models.ForeignKey(AssetLoan, on_delete=models.CASCADE, related_name="approval_records")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    approved = models.BooleanField("是否通过")
    comment = models.TextField("审批意见", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "审批记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]


class AssetStatusLog(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "资产状态变更日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]


class Attachment(models.Model):
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = verbose_name
