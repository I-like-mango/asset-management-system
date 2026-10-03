import logging

from django.http import JsonResponse

from common.exceptions import BusinessError

logger = logging.getLogger(__name__)


class BusinessExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, BusinessError):
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": exception.message}, status=400)
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.error(request, exception.message)
            return redirect(request.META.get("HTTP_REFERER") or "dashboard")
        logger.exception("Unhandled exception")
        return None
