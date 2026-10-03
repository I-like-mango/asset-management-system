def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_operation(request, action: str, module: str, object_id="", object_repr="", detail=None):
    from audit.models import OperationLog

    user = request.user if request.user.is_authenticated else None
    OperationLog.objects.create(
        user=user,
        action=action,
        module=module,
        object_id=str(object_id),
        object_repr=object_repr[:255],
        detail=detail or {},
        ip_address=get_client_ip(request),
    )
