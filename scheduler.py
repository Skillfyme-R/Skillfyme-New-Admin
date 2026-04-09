from core.services.scheduler_service import start_scheduler

if __name__ == "__main__":
    start_scheduler()

    import time
    while True:
        time.sleep(60)