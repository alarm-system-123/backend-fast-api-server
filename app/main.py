"""Main file"""
import asyncio
import json
import uvicorn
from fastapi import FastAPI

from app.mqtt import mqtt, sensors_cache, send_mqtt_command
from app.routers import system, groups
from app.routers import sensors
from app.routers.system import system_state

app = FastAPI(title="Smart Home IoT Server")
mqtt.init_app(app)
app.include_router(system.router)
app.include_router(sensors.router)
app.include_router(groups.router)

@mqtt.on_connect()
def connect(client, flags, rc, properties): # pylint: disable=W0613
    """Connect"""
    if rc != 0:
        print(f"❌ Помилка підключення: {rc}")
        return
    print(f"✅ Connected: {client}")

    client.subscribe("+/system/gateway/status")  # Статус заліза
    client.subscribe("+/system/mode/status")  # Статус охорони
    client.subscribe("+/alarm/status")  # Старий топік (для сумісності)
    client.subscribe("+/alarm/sensors")  # Датчики
    asyncio.create_task(send_mqtt_command("cmd", "system_status"))

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):  # pylint: disable=W0613
    """Unparse message"""
    try:
        data = json.loads(payload.decode())
        topic_parts = topic.split("/")

        if len(topic_parts) == 4 and topic_parts[1] == "system":
            device_id = topic_parts[0]
            sub_system = topic_parts[2]  # "gateway" або "mode"

            if sub_system == "gateway" and topic_parts[3] == "status":
                print(f"🔌 Зміна статусу шлюзу {device_id}: {data}")
                system_state["gateway_status"] = data.get("gateway_status", "offline")
                system_state["device"] = data.get("device", "unknown")

            elif sub_system == "mode" and topic_parts[3] == "status":
                print(f"🛡 Зміна режиму охорони {device_id}: {data}")
                system_state["mode"] = data.get("status", system_state.get("mode", "unknown"))

        elif len(topic_parts) == 3 and topic_parts[1] == "alarm":
            device_id = topic_parts[0]
            msg_type = topic_parts[2]
            print(f"📡 Отримано від Хаба {device_id} [{msg_type}]: {data}")

            if msg_type == "status" and "status" in data:
                system_state["mode"] = data["status"]

        elif len(topic_parts) == 3 and topic_parts[0] == "sensors":
            sensor_id = int(topic_parts[1])
            print(f"🌡 Оновлено кеш датчика {sensor_id}: {data}")
            sensors_cache[sensor_id] = data

        else:
            print(f"⚠️ Отримано невідомий топік [{topic}]: {data}")

    except json.JSONDecodeError:
        print(f"❌ Помилка парсингу JSON з топіка {topic}. Payload: {payload}")
    except Exception as e:  # pylint: disable=W0718
        print(f"❌ Системна помилка в on_message: {e}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
