import os
import django

# ✅ MUST BE FIRST (before ANY Django import)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edtech.settings')
django.setup()

# ✅ IMPORT AFTER SETUP
from core.services.scheduler_service import scheduler, reschedule_all_batches

if __name__ == "__main__":
    scheduler.start()
    reschedule_all_batches()

    import time
    while True:
        time.sleep(60)