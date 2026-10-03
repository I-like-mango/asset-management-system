import logging

from django.core.mail import send_mail
from django.utils import timezone

from django.conf import settings
from notifications.models import EmailLog

logger = logging.getLogger(__name__)


def queue_email(recipient_email: str, subject: str, body: str, dedup_key: str = ""):
    if dedup_key and EmailLog.objects.filter(dedup_key=dedup_key, status=EmailLog.STATUS_SENT).exists():
        return None
    log = EmailLog.objects.create(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        dedup_key=dedup_key,
    )
    send_email_log(log)
    return log


def send_email_log(log: EmailLog):
    try:
        send_mail(
            log.subject,
            log.body,
            settings.DEFAULT_FROM_EMAIL,
            [log.recipient_email],
            fail_silently=False,
        )
        log.status = EmailLog.STATUS_SENT
        log.sent_at = timezone.now()
        log.error_message = ""
        log.save(update_fields=["status", "sent_at", "error_message"])
    except Exception as exc:
        logger.exception("Email send failed")
        log.status = EmailLog.STATUS_FAILED
        log.error_message = str(exc)[:2000]
        log.retry_count += 1
        log.save(update_fields=["status", "error_message", "retry_count"])


def retry_failed_emails(max_retries=3):
    qs = EmailLog.objects.filter(status=EmailLog.STATUS_FAILED, retry_count__lt=max_retries)
    for log in qs[:50]:
        send_email_log(log)
