from accounts.services import get_user_menu_permissions, get_unread_message_count
from common.decorators import is_admin


def site_context(request):
    if not request.user.is_authenticated:
        return {}
    perms = get_user_menu_permissions(request.user)
    return {
        "site_is_admin": is_admin(request.user),
        "user_menu_permissions": perms,
        "unread_message_count": get_unread_message_count(request.user),
    }
