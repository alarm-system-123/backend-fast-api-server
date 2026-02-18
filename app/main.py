"""Main file"""
import json
import uvicorn
from fastapi import FastAPI

from app.mqtt import mqtt, sensors_cache
from app.routers import system
from app.routers import sensors

app = FastAPI(title="Smart Home IoT Server")
mqtt.init_app(app)
app.include_router(system.router)
app.include_router(sensors.router)

@mqtt.on_connect()
def connect(client, flags, rc, properties): # pylint: disable=W0613
    """Connect"""
    if rc != 0:
        print(f"❌ Помилка підключення: {rc}")
        return
    print(f"✅ Connected: {client}")

    mqtt.client.subscribe("+/alarm/status")
    mqtt.client.subscribe("sensors/+/status")

@mqtt.on_message()
async def message(client, topic, payload, qos, properties): # pylint: disable=W0613
    """Unparse massege"""
    try:
        data = json.loads(payload.decode())
        topic_parts = topic.split("/")

        if len(topic_parts) == 3 and topic_parts[1] == "alarm":
            device_id = topic_parts[0]
            msg_type = topic_parts[2]
            print(f"📡 Отримано від Хаба {device_id} [{msg_type}]: {data}")

        elif len(topic_parts) == 3 and topic_parts[0] == "sensors":
            sensor_id = int(topic_parts[1])
            print(f"🌡 Оновлено кеш датчика {sensor_id}: {data}")

            sensors_cache[sensor_id] = data

    except Exception as e: # pylint: disable=W0718
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
