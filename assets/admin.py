from django.contrib import admin

from assets.models import Asset, AssetCategory, AssetLoan, Attachment


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "warning_threshold", "is_active")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("asset_no", "name", "category", "status", "current_holder", "is_deleted")
    list_filter = ("status", "category", "is_deleted")
    search_fields = ("asset_no", "name", "serial_no")


@admin.register(AssetLoan)
class AssetLoanAdmin(admin.ModelAdmin):
    list_display = ("asset", "applicant", "status", "applied_at")


admin.site.register(Attachment)
