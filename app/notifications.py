"""Telegram handler"""
from datetime import datetime
import httpx
from app.database import gateways_collection
from app.telegram_bot import BOT_TOKEN

BOT_TOKEN = f"{BOT_TOKEN}"

last_alert_time = {}
COOLDOWN_SECONDS = 15


async def send_telegram_alarm(device_id: str, sensor_name: str):
    """Send telegram alarm"""
    hub = await gateways_collection.find_one({"_id": device_id})
    if not hub:
        return

    chat_ids = hub.get("telegram_chat_ids", [])
    if not chat_ids:
        print(f"⚠️ Для хаба {device_id} немає підписників у Telegram.")
        return

    now = datetime.now()
    cache_key = f"{device_id}_{sensor_name}"

    if cache_key in last_alert_time:
        seconds_passed = (now - last_alert_time[cache_key]).total_seconds()
        if seconds_passed < COOLDOWN_SECONDS:
            return

    last_alert_time[cache_key] = now

    text = (
        f"🚨 *ТРИВОГА!*\n\n"
        f"🏠 *Хаб:* `{device_id}`\n"
        f"📍 *Датчик:* {sensor_name}\n"
        f"⏰ *Час:* {now.strftime('%H:%M:%S')}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient() as client:
        for chat_id in chat_ids:
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    print(f"❌ Помилка відправки для {chat_id}: {response.text}")
            except Exception as e:
                print(f"❌ Помилка з'єднання з Telegram: {e}")
