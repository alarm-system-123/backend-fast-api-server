"""Mqtt module"""
import json
import asyncio
from typing import Optional
from fastapi_mqtt import FastMQTT, MQTTConfig

from app.database import gateways_collection, log_event
from app.notifications import send_telegram_alarm
from app.web_socket.web_socket import ws_manager
from common.config import MQTT_HOST, MQTT_USER, MQTT_PASSWORD

mqtt_config = MQTTConfig(
    host=MQTT_HOST,
    port=1883,
    keepalive=60,
    username=MQTT_USER,
    password=MQTT_PASSWORD
)
mqtt = FastMQTT(config=mqtt_config)


@mqtt.on_connect()
def connect(client, _flags, rc, _properties):
    """Subscribe for valid topics"""
    if rc != 0:
        print(f"❌ Помилка підключення до MQTT: {rc}")
        return

    print(f"✅ MQTT Connected: {client}")
    mqtt.client.subscribe("+/system/gateway/status")
    mqtt.client.subscribe("+/system/mode/status")
    mqtt.client.subscribe("+/system/events")
    mqtt.client.subscribe("+/sensors/+/status")


async def send_mqtt_command(
    device_id: str, cmd: str, action: str, sensor_id: Optional[int] = None, **kwargs
):
    """Send command to mqtt with optional arbitrary parameters"""
    payload = {"cmd": cmd, "action": action}

    if sensor_id is not None:
        payload["id"] = sensor_id

    payload.update(kwargs)

    topic = f"{device_id}/alarm/commands"

    print(f"🚀 ВІДПРАВЛЯЮ В MQTT [{topic}]: {json.dumps(payload)}")
    try:
        if getattr(mqtt.client, "_connection", None) is None:
            print("❌ Помилка: MQTT клієнт не підключений до брокера (Mosquitto)!")
            return

        mqtt.publish(topic, json.dumps(payload))
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Критична помилка при відправці MQTT: {e}")


async def _update_and_broadcast_system(device_id: str, db_update: dict, ws_state_payload: dict):
    """Update system status to database using WebSocket"""
    await gateways_collection.update_one(
        {"_id": device_id},
        {"$set": db_update},
        upsert=True
    )
    asyncio.create_task(ws_manager.broadcast_to_device(
        device_id=device_id,
        message={"event": "system_update", "system_state": ws_state_payload}
    ))


async def handle_system_message(device_id: str, sub_system: str, topic_parts: list, data: dict):
    """System message handler"""

    if sub_system == "gateway" and len(topic_parts) == 4 and topic_parts[3] == "status":
        print(f"🔌 Зміна статусу шлюзу {device_id}: {data}")
        new_status = data.get("gateway_status", "offline")

        status_ua = "в мережі" if new_status == "online" else "втратив зв'язок з інтернетом"
        await log_event(
            device_id=device_id,
            event_type="info" if new_status == "online" else "network",
            title="Статус хаба",
            message=f"Системний хаб {status_ua}"
        )

        await _update_and_broadcast_system(
            device_id=device_id,
            db_update={
                "system_state.gateway_status": new_status,
                "system_state.device": data.get("device", "unknown")
            },
            ws_state_payload={"gateway_status": new_status}
        )

    elif sub_system == "mode" and len(topic_parts) == 4 and topic_parts[3] == "status":
        print(f"🛡 Зміна режиму охорони {device_id}: {data}")
        new_mode = data.get("mode")

        mode_names = {"armed": "Повна охорона",
                      "disarmed": "Знято з охорони",
                      "partial": "Нічний режим"}
        mode_ua = mode_names.get(new_mode, new_mode)
        await log_event(
            device_id=device_id,
            event_type="system",
            title="Зміна режиму",
            message=f"Систему переведено в режим: {mode_ua}"
        )

        await _update_and_broadcast_system(
            device_id=device_id,
            db_update={"system_state.mode": new_mode},
            ws_state_payload={"mode": new_mode}
        )

    elif sub_system == "events":
        event_type = data.get("event")
        if event_type == "new_device_paired":
            print(f"🎉 Новий пристрій успішно спарено на хабі {device_id}!")

            await log_event(
                device_id=device_id,
                event_type="system",
                title="Новий пристрій",
                message="Успішно підключено новий датчик"
            )

            await _update_and_broadcast_system(
                device_id=device_id,
                db_update={"system_state.mode": "disarmed"},
                ws_state_payload={"mode": "disarmed"}
            )
        elif event_type == "alarm":
            sensor_name = data.get("sensor_name", "Невідомий датчик")

            print(
                f"🚨 БЕКЕНД ОТРИМАВ ТРИВОГУ! "
                f"Хаб: {device_id}, Датчик: {sensor_name}"
            )

            await log_event(
                device_id=device_id,
                event_type="alarm",
                title="🚨 Тривога!",
                message=f"Спрацював датчик: {sensor_name}"
            )

            await send_telegram_alarm(device_id=device_id, sensor_name=sensor_name)


async def handle_sensor_message(device_id: str, sensor_id: str, data: dict):
    """Sensor status handler"""
    old_doc = await gateways_collection.find_one({"_id": device_id})
    old_sensor_data = old_doc.get("sensors", {}).get(sensor_id, {}) if old_doc else {}

    await gateways_collection.update_one(
        {"_id": device_id},
        {"$set": {f"sensors.{sensor_id}": data}},
        upsert=True
    )

    doc = await gateways_collection.find_one({"_id": device_id})
    current_hub_sensors = list(doc.get("sensors", {}).values())

    asyncio.create_task(ws_manager.broadcast_to_device(
        device_id=device_id,
        message={
            "event": "sensor_update",
            "sensors": current_hub_sensors
        }
    ))

    print(f"🌡 Оновлено датчик {sensor_id} ({data.get('name')}): Стан {data.get('state')}")

    sensor_name = data.get('name', f'Датчик {sensor_id}')
    current_mode = doc.get("system_state", {}).get("mode")

    if data.get("state") != old_sensor_data.get("state"):
        if data.get("state") is True and current_mode == "disarmed":
            await log_event(
                device_id=device_id,
                event_type="info",
                title="Спрацювання",
                message=f"{sensor_name}: відкрито / виявлено рух"
            )

    new_bat = data.get("bat", 100)
    old_bat = old_sensor_data.get("bat", 100)
    if isinstance(new_bat, (int, float)) and new_bat < 15 <= old_bat:
        await log_event(
            device_id=device_id,
            event_type="warning",
            title="Низький заряд батареї",
            message=f"{sensor_name}: залишилось {new_bat}%"
        )

    new_online = data.get("online", True)
    old_online = old_sensor_data.get("online", True)
    if new_online is False and old_online is True:
        await log_event(
            device_id=device_id,
            event_type="warning",
            title="Втрата зв'язку",
            message=f"{sensor_name} перейшов в офлайн"
        )
    elif new_online is True and old_online is False:
        await log_event(
            device_id=device_id,
            event_type="info",
            title="Зв'язок відновлено",
            message=f"{sensor_name} знову в мережі"
        )


@mqtt.on_message()
async def message(_client, topic, payload, _qos, _properties):
    """Unparse message and trigger logic"""
    try:
        data = json.loads(payload.decode())
        topic_parts = topic.split("/")

        # 1. system massage handler
        if len(topic_parts) >= 3 and topic_parts[1] == "system":
            device_id = topic_parts[0]
            sub_system = topic_parts[2]
            await handle_system_message(device_id, sub_system, topic_parts, data)

        # 2. sensor message handler
        elif len(topic_parts) == 4 and topic_parts[1] == "sensors" and topic_parts[3] == "status":
            device_id = topic_parts[0]
            sensor_id = str(topic_parts[2])
            await handle_sensor_message(device_id, sensor_id, data)

        else:
            print(f"⚠️ Отримано невідомий топік [{topic}]: {data}")

    except json.JSONDecodeError:
        print(
            f"❌ Помилка парсингу JSON з топіка {topic}. "
            f"Payload: {payload.decode('utf-8', errors='ignore')}"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Системна помилка в on_message: {e}")
