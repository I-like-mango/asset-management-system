from django.db.models import Q

from assets.models import Asset


def filter_assets(queryset, params, *, for_user=None):
    """按查询参数筛选资产；for_user 非空时仅返回该用户领用的资产。"""
    if for_user is not None:
        queryset = queryset.filter(current_holder=for_user, is_deleted=False)

    category = params.get("category")
    status = params.get("status")
    keyword = params.get("q", "").strip()
    loaned_from = params.get("loaned_from")
    loaned_to = params.get("loaned_to")
    due_from = params.get("due_from")
    due_to = params.get("due_to")
    overdue = params.get("overdue")

    if category:
        queryset = queryset.filter(category_id=category)
    if status:
        queryset = queryset.filter(status=status)
    if keyword:
        queryset = queryset.filter(
            Q(asset_no__icontains=keyword)
            | Q(name__icontains=keyword)
            | Q(brand__icontains=keyword)
            | Q(model__icontains=keyword)
            | Q(serial_no__icontains=keyword)
        )
    if loaned_from:
        queryset = queryset.filter(loaned_at__date__gte=loaned_from)
    if loaned_to:
        queryset = queryset.filter(loaned_at__date__lte=loaned_to)
    if due_from:
        queryset = queryset.filter(due_at__date__gte=due_from)
    if due_to:
        queryset = queryset.filter(due_at__date__lte=due_to)
    if overdue == "1":
        from django.utils import timezone

        queryset = queryset.filter(status="loaned", due_at__lt=timezone.now())

    return queryset
