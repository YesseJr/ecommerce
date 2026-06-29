from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


def role_required(*roles):
    """
    Decorator that enforces role-based access control.
    Superusers always bypass role checks.
    Redirects to dashboard with an error message on access denial.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            # Django superusers bypass all role restrictions
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(
                    request,
                    "Access denied — you don't have permission to view this page."
                )
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


# Convenience aliases
# CRM modules: contacts, leads, deals, companies, inventory, reports, expenses
crm_required = role_required('admin', 'manager')

# Sales / POS — cashiers and managers only; admin is excluded
sales_required = role_required('manager', 'cashier')

# Admin-only sections
admin_required = role_required('admin')

# Contacts: cashiers can list, view, and edit — but NOT create or delete
contacts_view_edit = role_required('admin', 'manager', 'cashier')
