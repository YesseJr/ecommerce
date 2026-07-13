from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_role_required(*allowed_checks):
    """
    Restricts a view to users passing at least one of the given role checks.
    Each check is the name of a boolean property on User, e.g. 'is_moderator'.
    Superusers always pass (see User.is_moderator/is_support/is_finance,
    which already return True for superusers).

    Usage:
        @staff_role_required('is_moderator')
        def moderator_dashboard(request): ...

        @staff_role_required('is_moderator', 'is_admin')
        def shared_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')

            if not any(getattr(request.user, check, False) for check in allowed_checks):
                messages.error(request, "You don't have access to that area.")
                return redirect('staff:hub')

            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
