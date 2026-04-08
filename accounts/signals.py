"""
accounts/signals.py
--------------------
Post-login signal: keeps UserProfile.role in sync with WhitelistEntry.role
every time a user logs in (covers both Google OAuth and password login).
"""

import logging

from allauth.account.signals import user_logged_in
from django.dispatch import receiver

from accounts.adapters import _sync_profile, _ensure_super_admin_in_whitelist

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Sync role from whitelist on every login."""
    _ensure_super_admin_in_whitelist()
    _sync_profile(user)
    logger.info('User logged in: %s', user.email)