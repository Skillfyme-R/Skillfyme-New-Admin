"""
core/views/auth_views.py
-------------------------
COMPATIBILITY SHIM — real login/logout logic has moved to accounts/views.py.

These imports are kept so that any code that still imports from
core.views.auth_views doesn't break (e.g. existing middleware or tests).

is_authenticated() is kept because core middleware still calls it;
once all callers are migrated to request.user.is_authenticated it can
be removed.
"""

from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect


# ── Kept for backward compatibility (used by some existing helper fns) ────────

def is_authenticated(request) -> bool:
    """Returns True if the request has a valid Django session user."""
    return request.user.is_authenticated


# ── Views now delegate to accounts app ───────────────────────────────────────

def login_view(request):
    from accounts.views import login_view as _login
    return _login(request)


def logout_view(request):
    auth_logout(request)
    return redirect('/login/')