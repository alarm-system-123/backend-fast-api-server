"""Main file"""
import asyncio
import json
import uvicorn
from fastapi import FastAPI, WebSocketDisconnect
from starlette.websockets import WebSocket

from app.mock import get_system_state_for_device, get_sensors_for_device
from app.mqtt import mqtt, sensors_cache, send_mqtt_command
from app.routers import system
from app.routers import sensors
from app.routers.system import system_state
from app.web_socket.web_socket import ConnectionManager

app = FastAPI(title="Smart Home IoT Server")
mqtt.init_app(app)
app.include_router(system.router)
app.include_router(sensors.router)

ws_manager = ConnectionManager()


@mqtt.on_connect()
def connect(client, flags, rc, properties):  # pylint: disable=W0613
    """Connect"""
    if rc != 0:
        print(f"❌ Помилка підключення: {rc}")
        return
    print(f"✅ Connected: {client}")

    # Системні топіки
    client.subscribe("+/system/gateway/status")  # Статус заліза
    client.subscribe("+/system/mode/status")  # Статус охорони

    client.subscribe("+/sensors/+/status")

    asyncio.create_task(send_mqtt_command("cmd", "system_status"))

# Додаємо {device_id} в URL
@app.websocket("/ws/state/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await ws_manager.connect(websocket, device_id)
    try:
        current_system_state = get_system_state_for_device(device_id)
        current_sensors = get_sensors_for_device(device_id)

        await websocket.send_json({
            "event": "initial_state",
            "system_state": current_system_state,
            "sensors": current_sensors
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, device_id)

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):  # pylint: disable=W0613
    """Unparse message and trigger logic"""
    try:
        data = json.loads(payload.decode())
        topic_parts = topic.split("/")

        # ==========================================
        # 1. ГІЛКА СИСТЕМНИХ ПОВІДОМЛЕНЬ (ХАБ)
        # ==========================================
        if len(topic_parts) == 4 and topic_parts[1] == "system":
            device_id = topic_parts[0]
            sub_system = topic_parts[2]

            if sub_system == "gateway" and topic_parts[3] == "status":
                print(f"🔌 Зміна статусу шлюзу {device_id}: {data}")

                new_status = data.get("gateway_status", "offline")
                system_state["gateway_status"] = new_status
                system_state["device"] = data.get("device", "unknown")
                asyncio.create_task(ws_manager.broadcast_to_device(
                    device_id=device_id,
                    message={
                        "event": "system_update",
                        "system_state": {
                            "gateway_status": new_status
                        }
                    }
                ))
            elif sub_system == "mode" and topic_parts[3] == "status":
                print(f"🛡 Зміна режиму охорони {device_id}: {data}")
                device_id = topic_parts[0]
                system_state["mode"] = data.get("status", system_state.get("mode", "unknown"))
                asyncio.create_task(ws_manager.broadcast_to_device(
                    device_id=device_id,
                    message={
                        "event": "system_update",
                        "system_state": {"mode": data.get("status")}
                    }
                ))

        # ==========================================
        # 2. ГІЛКА ДАТЧИКІВ ТА ЛОГІКА ТРИВОГИ
        # ==========================================
        # УВАГА: Цей elif тепер на тому ж рівні, що й найперший if!
        elif len(topic_parts) == 4 and topic_parts[1] == "sensors" and topic_parts[3] == "status":
            device_id = topic_parts[0]  # Витягуємо MAC-адресу хаба
            sensor_id = int(topic_parts[2])  # ID датчика

            # 1. ІНІЦІАЛІЗАЦІЯ КЕШУ ДЛЯ ХАБА
            if device_id not in sensors_cache:
                sensors_cache[device_id] = {}

            # 2. ОНОВЛЕННЯ ДАНИХ
            sensors_cache[device_id][sensor_id] = data

            # 3. ВІДПРАВКА НА ТЕЛЕФОН
            current_hub_sensors = list(sensors_cache[device_id].values())

            asyncio.create_task(ws_manager.broadcast_to_device(
                device_id=device_id,
                message={
                    "event": "sensor_update",
                    "sensors": current_hub_sensors
                }
            ))

            print(f"🌡 Оновлено датчик {sensor_id} ({data.get('name')}): Стан {data.get('state')}")

            # --- БІЗНЕС-ЛОГІКА: ПЕРЕВІРКА НА ТРИВОГУ ---
            sensor_triggered = data.get("state") == True
            current_mode = system_state.get("mode")

            if sensor_triggered:
                if current_mode in ["armed", "armed_partial", "armed_group"]:
                    print(f"🚨 ТРИВОГА! Спрацював датчик: {data.get('name')}")

        # Зовнішній else для невідомих топіків
        else:
            print(f"⚠️ Отримано невідомий топік [{topic}]: {data}")

    except json.JSONDecodeError:
        print(f"❌ Помилка парсингу JSON з топіка {topic}. Payload: {payload.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
