import asyncio
from datetime import datetime, timedelta
from discord.ext import tasks

def parse_cron_schedule(cron_schedule):
    """
    Parses a crontab-like schedule string.

    Args:
        cron_schedule (str): Crontab-like schedule string (e.g., "0 17 * * 5")

    Returns:
        dict: Parsed schedule with keys 'minute', 'hour', 'day_of_month', 'month', 'day_of_week'
    """
    minute, hour, day_of_month, month, day_of_week = cron_schedule.split()
    return {
        "minute": int(minute),
        "hour": int(hour),
        "day_of_month": day_of_month,
        "month": month,
        "day_of_week": int(day_of_week)
    }

def time_until_next_schedule(parsed_schedule):
    """
    Calculates the time until the next scheduled run based on the parsed schedule.

    Args:
        parsed_schedule (dict): Parsed schedule with keys 'minute', 'hour', 'day_of_month', 'month', 'day_of_week'

    Returns:
        float: Time in seconds until the next scheduled run
    """
    now = datetime.now()
    target = now.replace(minute=parsed_schedule['minute'], hour=parsed_schedule['hour'], second=0, microsecond=0)
    
    while target.weekday() != parsed_schedule['day_of_week']:
        target += timedelta(days=1)
    
    if target < now:
        target += timedelta(days=7)
    
    return (target - now).total_seconds()

def schedule(cron_schedule):
    """
    Decorator to schedule a task function based on the crontab-like schedule.

    Args:
        cron_schedule (str): Crontab-like schedule string (e.g., "0 17 * * 5")
    """
    def decorator(func):
        parsed_schedule = parse_cron_schedule(cron_schedule)

        async def scheduled_task():
            await asyncio.sleep(time_until_next_schedule(parsed_schedule))
            while True:
                await func()
                await asyncio.sleep(time_until_next_schedule(parsed_schedule))

        async def start_task(bot):
            await bot.wait_until_ready()
            bot.loop.create_task(scheduled_task())

        func.start_task = start_task
        return func
    return decorator
