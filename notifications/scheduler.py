import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)

_scheduler = None


def daily_reminder_job():
    from notifications.services import email_service, reminder_service

    reminder_service.scan_due_reminders()
    reminder_service.scan_stock_warnings()
    email_service.retry_failed_emails()


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    try:
        scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.add_job(
            daily_reminder_job,
            trigger="cron",
            hour=8,
            minute=0,
            id="daily_asset_reminder",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
        _scheduler = scheduler
        logger.info("APScheduler started")
    except Exception:
        logger.exception("Failed to start APScheduler")
