"""
edtech/urls.py
--------------
Root URL configuration.

CHANGES vs original:
  • Added allauth URLs (Google OAuth flow)
  • Added accounts URLs (whitelist management, user dashboard)
  • Added instructors URLs (instructor CRUD + batch costing API)
  • /login/ now delegates to accounts.views (Google + fallback password)
  • /logout/ now delegates to accounts.views (allauth-aware)
  • All existing batch / cancel / log / dashboard URLs UNCHANGED.
"""

from django.urls import path, include
from django.shortcuts import redirect

from core.views import batch_views, cancel_views, log_views, dashboard_views
from accounts import views as account_views
from instructors import views as instructor_views

urlpatterns = [
    # ── Root redirect (unchanged) ─────────────────────────────────────────
    path('', lambda request: redirect('/login/', permanent=False)),

    # ── Auth — NEW: delegates to accounts app ────────────────────────────
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),

    # ── allauth OAuth (Google callback lives here) ────────────────────────
    path('accounts/', include('allauth.urls')),

    # ── Super-admin user management ───────────────────────────────────────
    path('admin/users/', account_views.user_list, name='user-list'),
    path('admin/users/create/', account_views.user_create, name='user-create'),
    path('admin/users/<int:pk>/edit/', account_views.user_edit, name='user-edit'),
    path('admin/users/<int:pk>/delete/', account_views.user_delete, name='user-delete'),

    # ── Health (unchanged) ────────────────────────────────────────────────
    path('health/', batch_views.health_view, name='health'),

    # ── API — batch (unchanged; upload-learners MUST precede <batch_code>) ─
    path('api/batch/create/', batch_views.create_batch, name='batch-create'),
    path('api/batch/upload-learners/', batch_views.upload_learners, name='batch-upload-learners'),
    path('api/batch/<str:batch_code>/', batch_views.batch_detail, name='batch-detail'),
    path('api/batches/', batch_views.list_batches, name='batch-list'),

    # ── API — cancellations / postponements (unchanged) ───────────────────
    path('api/batch/<str:batch_code>/cancel-class/', cancel_views.cancel_class_view, name='cancel-class'),
    path('api/batch/<str:batch_code>/postpone-class/', cancel_views.postpone_class_view, name='postpone-class'),

    # ── API — email logs (unchanged) ──────────────────────────────────────
    path('api/batch/<str:batch_code>/email-logs/', log_views.get_email_logs, name='email-logs'),
    path('api/dashboard/email-logs/sent-today/', log_views.api_sent_today, name='api-sent-today'),
    path('api/dashboard/email-logs/failed-today/', log_views.api_failed_today, name='api-failed-today'),

    # ── Dashboard HTML pages (unchanged) ──────────────────────────────────
    path('dashboard/', dashboard_views.dashboard, name='dashboard'),
    path('dashboard/email-logs/sent-today/', dashboard_views.sent_today_page, name='sent-today-page'),
    path('dashboard/email-logs/failed-today/', dashboard_views.failed_today_page, name='failed-today-page'),
    path('dashboard/email-logs/last-sent/', dashboard_views.last_sent_page, name='last-sent-page'),
    path('dashboard/batches/', dashboard_views.batches_page, name='batches-page'),
    path('dashboard/batch/<str:batch_code>/', dashboard_views.batch_detail_dashboard, name='batch-detail-dashboard'),

    # ── NEW: Instructor Management ────────────────────────────────────────
    path('instructors/', instructor_views.instructor_list, name='instructor-list'),
    path('instructors/create/', instructor_views.instructor_create, name='instructor-create'),
    path('instructors/<int:pk>/edit/', instructor_views.instructor_edit, name='instructor-edit'),
    path('instructors/<int:pk>/delete/', instructor_views.instructor_delete, name='instructor-delete'),
    path('instructors/report/', instructor_views.instructor_payout_report, name='instructor-payout-report'),

    # ── NEW: Instructor API (used by batch form auto-fill) ────────────────
    path('api/instructors/', instructor_views.api_instructor_list, name='api-instructor-list'),
    path('api/instructors/<int:pk>/', instructor_views.api_instructor_detail, name='api-instructor-detail'),
    path('api/batch/<str:batch_code>/cost/', instructor_views.api_batch_cost, name='api-batch-cost'),
]