"""sheduler"""
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import db
from app.mqtt import send_mqtt_command
scheduler = AsyncIOScheduler()


async def check_and_execute_schedules():
    """check and execute schedules"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = now.weekday()

    cursor = db.schedules.find({
        "time": current_time,
        "days": current_day,
        "is_enabled": True
    })

    print(f"🔄 Перевірка... Час сервера: {current_time}, День: {current_day}")

    async for schedule in cursor:
        device_id = schedule["device_id"]
        action = schedule["action"]

        print(f"⏰ [Scheduler] Виконую {action} для хаба {device_id}")
        await send_mqtt_command(device_id=device_id, cmd="cmd", action=action)


def start_scheduler():
    """start scheduler"""
    if not scheduler.running:
        scheduler.add_job(check_and_execute_schedules, "cron", minute="*", second="0")
        scheduler.start()
        print("✅ Планувальник розкладів запущено")
