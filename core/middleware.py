"""
core/middleware.py
------------------
DEPRECATED — replaced by accounts.middleware.WhitelistMiddleware.

This file is kept so that any remaining imports don't break,
but the class does nothing (authentication is handled by allauth +
WhitelistMiddleware now registered in settings.MIDDLEWARE).

Remove this file entirely once all references are cleaned up.
"""


class LoginRequiredMiddleware:
    """No-op stub — real enforcement is in accounts.middleware.WhitelistMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)