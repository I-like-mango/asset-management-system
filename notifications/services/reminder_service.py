from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from assets.models import Asset
from common.constants import AssetStatus, MessageType
from common.decorators import is_admin
from notifications.models import ReminderLog
from notifications.services import message_service


def _days_until_due(asset, today):
    if not asset.due_at:
        return None
    return (asset.due_at.date() - today).days


def _reminder_kind(days_until):
    if days_until == 7:
        return "before_7"
    if days_until == 3:
        return "before_3"
    if days_until == 1:
        return "before_1"
    if days_until == 0:
        return "due_today"
    return None


def scan_due_reminders():
    today = timezone.localdate()
    assets = Asset.objects.filter(is_deleted=False, status=AssetStatus.LOANED, current_holder__isnull=False)
    for asset in assets.select_related("current_holder"):
        days = _days_until_due(asset, today)
        if days is None:
            continue
        holder = asset.current_holder
        kinds = []
        kind = _reminder_kind(days)
        if kind:
            kinds.append(kind)
        if days < 0 and abs(days) % 3 == 0:
            kinds.append("overdue_every_3")

        for rk in kinds:
            if ReminderLog.objects.filter(
                asset=asset, user=holder, reminder_kind=rk, remind_date=today
            ).exists():
                continue
            title = f"资产到期提醒：{asset.asset_no}"
            if rk.startswith("before") or rk == "due_today":
                content = f"您领用的 {asset.name} 将于 {asset.due_at.strftime('%Y-%m-%d %H:%M')} 到期，请及时归还或续借。"
            else:
                content = f"您领用的 {asset.name} 已逾期，请尽快归还。"
            message_service.send_message(
                holder,
                title=title,
                content=content,
                msg_type=MessageType.REMINDER,
                related_key=f"reminder:{asset.pk}:{rk}:{today}",
                send_email=True,
            )
            ReminderLog.objects.create(
                asset=asset, user=holder, reminder_kind=rk, remind_date=today
            )
            for admin in User.objects.filter(is_active=True):
                if is_admin(admin):
                    message_service.send_message(
                        admin,
                        title=f"[管理] {title}",
                        content=content,
                        msg_type=MessageType.REMINDER,
                        related_key=f"admin_reminder:{asset.pk}:{rk}:{today}",
                        send_email=False,
                    )


def scan_stock_warnings():
    from assets.models import AssetCategory
    from notifications.models import Message

    today = timezone.localdate()
    from django.contrib.auth.models import User

    for cat in AssetCategory.objects.filter(is_active=True):
        cnt = cat.in_stock_count
        if cnt <= cat.warning_threshold:
            key = f"stock:{cat.pk}:{today}"
            for admin in User.objects.filter(groups__name="ADMIN", is_active=True):
                if Message.objects.filter(recipient=admin, related_key=key).exists():
                    continue
                message_service.send_message(
                    admin,
                    title=f"库存预警：{cat.name}",
                    content=f"分类 {cat.name} 在库数量 {cnt}，低于阈值 {cat.warning_threshold}。",
                    msg_type=MessageType.STOCK,
                    related_key=key,
                )
