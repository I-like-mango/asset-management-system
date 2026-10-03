from django.contrib.auth.models import Group, User

from accounts.models import GroupPermission, UserProfile
from common.constants import (
    ADMIN_DEFAULT_PERMISSIONS,
    GROUP_ADMIN,
    GROUP_USER,
    PERMISSION_CODES,
    USER_DEFAULT_PERMISSIONS,
)
from common.decorators import is_admin


def user_has_permission(user, perm_code: str) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or is_admin(user):
        return True
    group_ids = user.groups.values_list("id", flat=True)
    return GroupPermission.objects.filter(group_id__in=group_ids, permission_code=perm_code).exists()


def get_user_permissions(user) -> set:
    if user.is_superuser or is_admin(user):
        return set(PERMISSION_CODES.keys())
    group_ids = user.groups.values_list("id", flat=True)
    return set(
        GroupPermission.objects.filter(group_id__in=group_ids).values_list("permission_code", flat=True)
    )


def get_user_menu_permissions(user) -> list:
    perms = get_user_permissions(user)
    return [code for code in PERMISSION_CODES if code.startswith("menu.") and code in perms]


def get_unread_message_count(user) -> int:
    from notifications.models import Message

    return Message.objects.filter(recipient=user, is_read=False).count()


def ensure_default_groups():
    admin_group, _ = Group.objects.get_or_create(name=GROUP_ADMIN)
    user_group, _ = Group.objects.get_or_create(name=GROUP_USER)
    GroupPermission.objects.filter(group=admin_group).delete()
    GroupPermission.objects.filter(group=user_group).delete()
    for code in ADMIN_DEFAULT_PERMISSIONS:
        GroupPermission.objects.create(group=admin_group, permission_code=code)
    for code in USER_DEFAULT_PERMISSIONS:
        GroupPermission.objects.create(group=user_group, permission_code=code)
    return admin_group, user_group


def sync_group_permissions(group: Group, permission_codes: list):
    GroupPermission.objects.filter(group=group).delete()
    for code in permission_codes:
        if code in PERMISSION_CODES:
            GroupPermission.objects.create(group=group, permission_code=code)


def get_or_create_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile
