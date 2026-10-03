from django.core.management.base import BaseCommand

from notifications.services import email_service, reminder_service


class Command(BaseCommand):
    help = "手动执行到期提醒、库存预警与失败邮件重试（供测试或 crontab）"

    def handle(self, *args, **options):
        reminder_service.scan_due_reminders()
        reminder_service.scan_stock_warnings()
        email_service.retry_failed_emails()
        self.stdout.write(self.style.SUCCESS("提醒任务执行完成"))
