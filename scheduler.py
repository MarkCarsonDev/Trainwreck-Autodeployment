from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

def schedule(cron_schedule):
    """
    Decorator to schedule a task function based on the crontab-like schedule.

    Args:
        cron_schedule (str): Crontab-like schedule string (e.g., "0 17 * * 5")
    """
    def decorator(func):
        trigger = CronTrigger.from_crontab(cron_schedule)
        scheduler.add_job(func, trigger, args=[func.bot])
        return func
    return decorator

def start_scheduler():
    scheduler.start()
