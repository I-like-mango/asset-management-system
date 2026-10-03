from django.utils import timezone

from common.constants import MessageType
from notifications.models import Message
from notifications.services import email_service


def send_message(
    user,
    title: str,
    content: str,
    msg_type=MessageType.SYSTEM,
    related_key: str = "",
    send_email: bool = False,
):
    msg = Message.objects.create(
        recipient=user,
        title=title,
        content=content,
        msg_type=msg_type,
        related_key=related_key,
    )
    if send_email and user.email:
        email_service.queue_email(
            user.email,
            title,
            content,
            dedup_key=related_key or f"msg:{msg.pk}",
        )
    return msg


def mark_read(message: Message):
    if not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save(update_fields=["is_read", "read_at"])


def mark_all_read(user):
    Message.objects.filter(recipient=user, is_read=False).update(is_read=True, read_at=timezone.now())
