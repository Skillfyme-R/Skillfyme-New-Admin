"""
accounts/middleware.py
-----------------------
WhitelistMiddleware — replaces the original LoginRequiredMiddleware.

Differences from original:
  • Uses request.user.is_authenticated (Django auth) instead of raw session key
  • Allows allauth OAuth callback paths through (accounts/*)
  • Still guards all protected paths in the same way
  • API paths (/api/*) now get a JSON 401 response instead of an HTML redirect,
    so fetch() calls in the frontend don't crash trying to parse HTML as JSON.

OPEN_PATHS remains a superset of the original so no existing behaviour breaks.
"""

import json
from django.shortcuts import redirect
from django.http import HttpResponse

OPEN_PATHS = {
    '/login', '/login/',
    '/logout', '/logout/',
    '/health', '/health/',
    # allauth OAuth endpoints must be open so the Google callback works
    '/accounts/',
}


def _is_open(path: str) -> bool:
    if path in OPEN_PATHS:
        return True
    # allauth sub-paths (e.g. /accounts/google/login/callback/)
    if path.startswith('/accounts/'):
        return True
    return False


class WhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not _is_open(request.path):
            if not request.user.is_authenticated:
                # API requests expect JSON — return 401 instead of HTML redirect
                if request.path.startswith('/api/'):
                    return HttpResponse(
                        json.dumps({'detail': 'Authentication required. Please log in.'}),
                        status=401,
                        content_type='application/json',
                    )
                return redirect('/login/')
        return self.get_response(request)
