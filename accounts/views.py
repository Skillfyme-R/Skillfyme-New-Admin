"""
accounts/views.py
-----------------
Auth views (login/logout) + Super-Admin user-management views.

login_view  — Shows login page with Google Sign-In button.
              Falls back to username/password for non-Google accounts.
              On password success: manually authenticates via Django auth.
logout_view — Clears session via allauth + Django.
user_list   — Super Admin: list all whitelist entries.
user_create — Super Admin: add new whitelist entry.
user_edit   — Super Admin: edit role / active status.
user_delete — Super Admin: remove whitelist entry.
"""

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.adapters import _ensure_super_admin_in_whitelist, _sync_profile
from accounts.decorators import super_admin_required
from accounts.models import Role, UserProfile, WhitelistEntry

logger = logging.getLogger(__name__)


# ── Auth ──────────────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def login_view(request):
    """
    GET  → Show login page (Google button + optional password form).
    POST → Username/password fallback login.
    """
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    error = request.GET.get('error')
    if error == 'access_denied':
        error_msg = 'Access not granted. Please contact your administrator.'
    else:
        error_msg = None

    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'error': error_msg})

    # POST — password fallback
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    # Try by email first, then by username
    try:
        db_user = User.objects.get(email__iexact=username)
        actual_username = db_user.username
    except User.DoesNotExist:
        actual_username = username

    user = authenticate(request, username=actual_username, password=password)
    if user is None:
        # Check if user exists but has no password (Google-only account)
        try:
            google_user = User.objects.get(email__iexact=username)
            if not google_user.has_usable_password():
                return render(request, 'accounts/login.html', {'error': 'This account uses Google Sign-In. Please use the "Sign in with Google" button above.'}, status=401)
        except User.DoesNotExist:
            pass
        logger.warning('Failed password login for username: %s', username)
        return render(request, 'accounts/login.html', {'error': 'Invalid username or password.'}, status=401)

    # Check whitelist
    _ensure_super_admin_in_whitelist()
    entry = None
    try:
        entry = WhitelistEntry.objects.get(email__iexact=user.email, is_active=True)
    except WhitelistEntry.DoesNotExist:
        logger.warning('Password login blocked — not in whitelist: %s', user.email)
        return render(request, 'accounts/login.html', {'error': 'Access not granted.'}, status=403)

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    _sync_profile(user)
    logger.info('Password login successful: %s', user.email)
    return redirect('/dashboard/')


def logout_view(request):
    auth_logout(request)
    return redirect('/login/')


# ── Super-Admin: User Management ──────────────────────────────────────────────

@super_admin_required
def user_list(request):
    entries = WhitelistEntry.objects.order_by('email')
    return render(request, 'accounts/user_list.html', {'entries': entries, 'roles': Role.choices})


@super_admin_required
@require_http_methods(['GET', 'POST'])
def user_create(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        role = request.POST.get('role', Role.AGENT)
        is_active = request.POST.get('is_active') == 'on'

        if not email:
            messages.error(request, 'Email is required.')
        elif WhitelistEntry.objects.filter(email=email).exists():
            messages.error(request, f'Email {email} is already whitelisted.')
        elif role not in Role.values:
            messages.error(request, 'Invalid role.')
        else:
            WhitelistEntry.objects.create(email=email, role=role, is_active=is_active)
            messages.success(request, f'{email} added to whitelist.')
            logger.info('Super admin %s added %s (role=%s) to whitelist', request.user.email, email, role)
            return redirect('user-list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Create',
        'roles': Role.choices,
        'entry': None,
    })


@super_admin_required
@require_http_methods(['GET', 'POST'])
def user_edit(request, pk):
    entry = get_object_or_404(WhitelistEntry, pk=pk)

    if request.method == 'POST':
        role = request.POST.get('role', entry.role)
        is_active = request.POST.get('is_active') == 'on'

        if role not in Role.values:
            messages.error(request, 'Invalid role.')
        else:
            entry.role = role
            entry.is_active = is_active
            entry.save(update_fields=['role', 'is_active', 'updated_at'])

            # Sync profile if user already exists
            try:
                django_user = User.objects.get(email__iexact=entry.email)
                _sync_profile(django_user)
            except User.DoesNotExist:
                pass

            messages.success(request, f'{entry.email} updated.')
            logger.info('Super admin %s updated whitelist entry for %s', request.user.email, entry.email)
            return redirect('user-list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Edit',
        'roles': Role.choices,
        'entry': entry,
    })


@super_admin_required
@require_http_methods(['POST'])
def user_delete(request, pk):
    entry = get_object_or_404(WhitelistEntry, pk=pk)

    # Prevent super admin from deleting their own account
    if entry.email.lower() == request.user.email.lower():
        messages.error(request, 'You cannot remove your own account.')
        return redirect('user-list')

    email = entry.email
    entry.delete()
    logger.info('Super admin %s removed %s from whitelist', request.user.email, email)
    messages.success(request, f'{email} removed from whitelist.')
    return redirect('user-list')