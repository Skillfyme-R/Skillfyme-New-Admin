"""
accounts/models.py
------------------
Whitelist-based access control + Role-Based Access.

Tables:
  whitelist_entries  — email, role, is_active (managed by Super Admin)
  user_profiles      — links Django User → whitelist entry + stores role

Roles (string choices, stored in both models for fast lookup):
  super_admin | admin | manager | tl | agent
"""

from django.contrib.auth.models import User
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    ADMIN = 'admin', 'Admin'
    MANAGER = 'manager', 'Manager'
    TL = 'tl', 'Team Lead'
    AGENT = 'agent', 'Agent'


class WhitelistEntry(models.Model):
    """
    The canonical list of users allowed to access the system.
    Managed exclusively by Super Admin.
    """
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AGENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'whitelist_entries'
        ordering = ['email']

    def __str__(self):
        return f'<WhitelistEntry {self.email!r} role={self.role} active={self.is_active}>'


class UserProfile(models.Model):
    """
    One-to-one extension of Django's User model.
    Created automatically when a whitelisted user first logs in.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AGENT)
    whitelist_entry = models.OneToOneField(
        WhitelistEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile',
    )

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f'<UserProfile {self.user.email!r} role={self.role}>'

    # ── Convenience helpers ──────────────────────────────────────────────

    @property
    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    @property
    def display_role(self):
        return Role(self.role).label if self.role else '—'