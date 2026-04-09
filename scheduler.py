import os
import django

# ✅ MUST BE FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edtech.settings')
django.setup()

from core.services.scheduler_service import scheduler, reschedule_all_batches

if __name__ == "__main__":
    scheduler.start()
    reschedule_all_batches()

    import time
    while True:
        time.sleep(60)