"""
accounts/adapters.py
---------------------
Custom allauth adapters that enforce the whitelist on every login attempt.

WhitelistSocialAccountAdapter  — called for Google OAuth logins
WhitelistAccountAdapter        — called for username/password logins

Both adapters:
  1. Look up the email in WhitelistEntry
  2. Raise ImmediateHttpResponse (→ /login/?error=access_denied) if not found or inactive
  3. On first login, create/update UserProfile with the whitelisted role
"""

import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import redirect

from accounts.models import WhitelistEntry, UserProfile, Role

logger = logging.getLogger(__name__)


def _get_whitelist_entry(email: str):
    """Return active WhitelistEntry for email, or None."""
    try:
        return WhitelistEntry.objects.get(email__iexact=email, is_active=True)
    except WhitelistEntry.DoesNotExist:
        return None


def _ensure_super_admin_in_whitelist():
    """
    Idempotently ensure the configured super-admin email is in the whitelist.
    Called on adapter init so it bootstraps itself on first deploy.
    """
    email = getattr(settings, 'SUPER_ADMIN_EMAIL', 'anand@skillfyme.in')
    WhitelistEntry.objects.get_or_create(
        email__iexact=email,
        defaults={'email': email, 'role': Role.SUPER_ADMIN, 'is_active': True},
    )


class WhitelistSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adapter for Google OAuth (and any other social provider)."""

    def is_open_for_signup(self, request, sociallogin):
        # Always return True here — the real whitelist check happens in pre_social_login below.
        # Without this override, allauth calls WhitelistAccountAdapter.is_open_for_signup(request)
        # with NO sociallogin arg, which always returns False and shows "Sign Up Closed".
        return True

    def pre_social_login(self, request, sociallogin):
        _ensure_super_admin_in_whitelist()

        email = sociallogin.account.extra_data.get('email', '').lower()
        if not email:
            logger.warning('Social login attempted with no email in payload')
            raise self.build_deny_response(request)

        entry = _get_whitelist_entry(email)
        if entry is None:
            logger.warning('Blocked non-whitelisted Google login: %s', email)
            raise self.build_deny_response(request)

        logger.info('Whitelisted Google login allowed: %s (role=%s)', email, entry.role)

    def build_deny_response(self, request):
        from allauth.exceptions import ImmediateHttpResponse
        return ImmediateHttpResponse(redirect('/login/?error=access_denied'))

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        _sync_profile(user)
        return user


class WhitelistAccountAdapter(DefaultAccountAdapter):
    """Adapter for username/password fallback logins."""

    def is_open_for_signup(self, request, sociallogin=None):
        # Block all direct self-registration (username/password signup)
        return False

    def authentication_failed(self, request, **kwargs):
        logger.warning('Password login failed for request from %s', request.META.get('REMOTE_ADDR'))
        super().authentication_failed(request, **kwargs)


def _sync_profile(user):
    """
    Create or update UserProfile to match the whitelist entry.
    Called after every successful login to keep roles in sync.
    """
    try:
        entry = WhitelistEntry.objects.get(email__iexact=user.email, is_active=True)
    except WhitelistEntry.DoesNotExist:
        logger.error('No active whitelist entry for logged-in user %s — this should not happen', user.email)
        return

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = entry.role
    profile.whitelist_entry = entry
    profile.save(update_fields=['role', 'whitelist_entry'])