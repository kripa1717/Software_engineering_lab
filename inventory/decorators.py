from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """R-15: restricts a view to Admin role only (vendor, report, forecast modules)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'Admin':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_or_admin_required(view_func):
    """R-15: allows both Admin and Staff (e.g. update stock, view alerts, dashboard)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ('Admin', 'Staff'):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
