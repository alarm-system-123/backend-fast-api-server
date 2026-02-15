"""Main file"""
import json
import uvicorn
from fastapi import FastAPI
from app.mqtt import mqtt
from app.routers import system

app = FastAPI(title="Smart Home IoT Server")

mqtt.init_app(app)

app.include_router(system.router)

@mqtt.on_connect()
def connect(client, flags, rc, properties): # pylint: disable=W0613
    """Connect to MQTT server"""

    if rc != 0:
        print(f"❌ Помилка підключення до брокера. Код: {rc}")
        return

    print(f"✅ Connected: {client}")

    mqtt.client.subscribe("+/alarm/status")
    mqtt.client.subscribe("+/alarm/sensors")

@mqtt.on_message()
async def message(client, topic, payload, qos, properties): # pylint: disable=W0613
    """ Decode message"""
    try:
        decoded_payload = payload.decode()
        data = json.loads(decoded_payload)

        topic_parts = topic.split("/")

        if len(topic_parts) < 3:
            print(f"⚠️ Невідомий формат топіка: {topic}")
            return

        device_id = topic_parts[0]  # MAC-адреса
        msg_type = topic_parts[2]  # status або sensors

        print(f"📡 Отримано від {device_id} [{msg_type}]: {data}")

        if msg_type == "status":
            # Тут код для оновлення статусу
            pass

        elif msg_type == "sensors":
            # Тут код для датчиків
            pass


    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"❌ Помилка обробки повідомлення: {e}")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
