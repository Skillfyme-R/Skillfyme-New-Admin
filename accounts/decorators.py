"""
accounts/decorators.py
-----------------------
Role-based access control decorators for view functions.

Usage:
    from accounts.decorators import require_role, super_admin_required

    @require_role('admin', 'super_admin')
    def my_view(request): ...

    @super_admin_required
    def admin_only_view(request): ...
"""

import functools

from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from accounts.models import Role


def require_role(*roles):
    """
    Decorator factory: allows users whose profile role is in `roles`.
    Redirects unauthenticated users to /login/.
    Returns 403 for authenticated users with insufficient role.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/')
            try:
                user_role = request.user.profile.role
            except AttributeError:
                return HttpResponseForbidden('No profile assigned.')
            if user_role not in roles:
                return HttpResponseForbidden(
                    f'Access denied. Required role: {", ".join(roles)}. Your role: {user_role}.'
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience shortcuts
super_admin_required = require_role(Role.SUPER_ADMIN)
admin_required = require_role(Role.SUPER_ADMIN, Role.ADMIN)
manager_required = require_role(Role.SUPER_ADMIN, Role.ADMIN, Role.MANAGER)