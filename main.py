"""Main file"""

import json
from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig
from mqttcommand import MQTTCommand

mqtt_config = MQTTConfig(
    host="localhost",
    port=1883,
    keepalive=60
)

app = FastAPI()
mqtt = FastMQTT(config=mqtt_config)
mqtt.init_app(app)

CONTROLLER_TOPIC = "00:70:07:24:26:D0/alarm/commands"

INCOMING_TOPIC = "00:70:07:24:26:D0/alarm/events"

SUB_TOPIC_STATUS = "+/alarm/status"
SUB_TOPIC_SENSORS = "+/alarm/sensors"

@mqtt.on_connect()
def connect(client, flags, rc, properties):
    """Connect to MQTT server"""
    print(f"Connected: {client}")
    mqtt.client.subscribe(SUB_TOPIC_STATUS)
    mqtt.client.subscribe(SUB_TOPIC_SENSORS)
    print("Підписалися на топіки: +/alarm/status та +/alarm/sensors")


@mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    """ Decode message"""
    try:
        decoded_payload = payload.decode()
        data = json.loads(decoded_payload)

        topic_parts = topic.split("/")

        device_id = topic_parts[0]  # Отримуємо MAC-адресу (AA:BB:CC...)
        msg_type = topic_parts[2]  # Отримуємо тип (status або sensors)

        print(f"📡 Отримано від {device_id} [{msg_type}]: {data}")

        # --- ЛОГІКА ОБРОБКИ ---
        if msg_type == "status":
            # Тут код для оновлення статусу системи (на охороні/знято)
            # Наприклад: save_status_to_db(device_id, data)
            pass

        elif msg_type == "sensors":
            # Тут код для оновлення показань датчиків
            # Наприклад: update_sensors_in_db(device_id, data)
            pass

    except Exception as e:
        print(f"Помилка обробки: {e}")


@app.post("/api/arm")
async def arm_system():
    """Arm system"""
    payload = MQTTCommand(cmd="cmd", action="arm")

    mqtt.publish(CONTROLLER_TOPIC, payload.json())

    return {"status": "command_sent", "action": "arm"}


@app.post("/api/disarm")
async def disarm_system():
    """Disarm system"""
    payload = MQTTCommand(cmd="cmd", action="disarm")
    mqtt.publish(CONTROLLER_TOPIC, payload.json())
    return {"status": "command_sent", "action": "disarm"}


@app.post("/api/partial")
async def partial_arm_system():
    """Partial arm, night schedule"""
    payload = MQTTCommand(cmd="cmd", action="partial")
    mqtt.publish(CONTROLLER_TOPIC, payload.json())
    return {"status": "command_sent", "action": "partial"}


if __name__ == "__main__":
    import uvicorn
    # Запускаємо сервер на порті 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
