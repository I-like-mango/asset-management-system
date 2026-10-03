from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from assets.models import Asset, AssetCategory, AssetLoan
from common.constants import AssetStatus


def dashboard_stats(for_user=None):
    qs = Asset.objects.filter(is_deleted=False)
    if for_user:
        qs = qs.filter(current_holder=for_user)

    total = qs.count()
    in_stock = qs.filter(status=AssetStatus.IN_STOCK).count()
    loaned = qs.filter(status=AssetStatus.LOANED).count()
    maintenance = qs.filter(status=AssetStatus.MAINTENANCE).count()
    scrapped = qs.filter(status=AssetStatus.SCRAPPED).count()
    now = timezone.now()
    overdue = qs.filter(status=AssetStatus.LOANED, due_at__lt=now).count()

    by_category = (
        qs.values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_status = (
        qs.values("status")
        .annotate(count=Count("id"))
    )
    status_labels = dict(AssetStatus.CHOICES)
    by_status_chart = [
        {"name": status_labels.get(item["status"], item["status"]), "value": item["count"]}
        for item in by_status
    ]
    by_type_chart = [{"name": item["category__name"], "value": item["count"]} for item in by_category]

    six_months_ago = now - timedelta(days=180)
    loan_trend = (
        AssetLoan.objects.filter(applied_at__gte=six_months_ago, status="approved")
        .annotate(month=TruncMonth("applied_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    loan_trend_data = [
        {"month": item["month"].strftime("%Y-%m") if item["month"] else "", "count": item["count"]}
        for item in loan_trend
    ]

    thirty_days = now + timedelta(days=30)
    due_trend = (
        Asset.objects.filter(
            is_deleted=False,
            status=AssetStatus.LOANED,
            due_at__gte=now - timedelta(days=1),
            due_at__lte=thirty_days,
        )
        .annotate(day=TruncDate("due_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    due_trend_data = [
        {"day": item["day"].strftime("%m-%d") if item["day"] else "", "count": item["count"]}
        for item in due_trend
    ]

    low_stock = []
    if not for_user:
        for cat in AssetCategory.objects.filter(is_active=True):
            cnt = cat.in_stock_count
            if cnt <= cat.warning_threshold:
                low_stock.append({"category": cat.name, "count": cnt, "threshold": cat.warning_threshold})

    return {
        "total": total,
        "in_stock": in_stock,
        "loaned": loaned,
        "maintenance": maintenance,
        "scrapped": scrapped,
        "overdue": overdue,
        "by_type_chart": by_type_chart,
        "by_status_chart": by_status_chart,
        "loan_trend": loan_trend_data,
        "due_trend": due_trend_data,
        "low_stock": low_stock,
    }
