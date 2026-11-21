"""Demo accounts for showing the app (demo day), logged in with one click from the login page."""
from django.conf import settings

from .models import User

# role -> (username, full name, email)
DEMO_ACCOUNTS = {
    User.Role.MANAGER: ('demo-manager', 'Demo Manager', 'manager@demo.ration'),
    User.Role.ACCOUNTANT: ('demo-accountant', 'Demo Accountant', 'accountant@demo.ration'),
    User.Role.CREATOR: ('demo-creator', 'Demo Creator', 'creator@demo.ration'),
}


def demo_login_enabled():
    return getattr(settings, 'DEMO_LOGIN', False)


def ensure_demo_accounts():
    """Create or refresh the three demo accounts. They have no usable password."""
    created = []
    for role, (username, full_name, email) in DEMO_ACCOUNTS.items():
        user, was_created = User.objects.get_or_create(
            email=email, defaults={'username': username, 'full_name': full_name, 'role': role},
        )
        changed = was_created or user.role != role or not user.is_active or user.has_usable_password()
        user.role, user.full_name, user.is_active = role, full_name, True
        user.set_unusable_password()
        if changed:
            user.save()
        if was_created:
            created.append(user)
    return created
