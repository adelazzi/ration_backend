from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(check):
    """Allow the view only for logged-in users where check(user) is true; others get a 403."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not check(request.user):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


manager_required = role_required(lambda user: user.is_manager)
price_reviewer_required = role_required(lambda user: user.can_review_prices)
config_viewer_required = role_required(lambda user: user.can_view_config)
