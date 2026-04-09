"""
core/apps.py
------------
Django AppConfig — starts APScheduler on Django startup.

The double-start guard uses RUN_MAIN (set by Django's auto-reloader in
development) to prevent the scheduler starting twice. In production
(gunicorn, no auto-reloader), RUN_MAIN is not set, so the normal
`not scheduler.running` guard is used with a threading.Event.
"""

import logging
import os
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)

# Threading event so we only start once even if ready() is called twice
_started = threading.Event()


class CoreConfig(AppConfig):
    name = 'core'
    default_auto_field = 'django.db.models.BigAutoField'
