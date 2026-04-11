"""Mqtt module"""
import json
from typing import Optional
from fastapi_mqtt import FastMQTT, MQTTConfig

from app.schema.system_state_schema import SystemState

mqtt_config = MQTTConfig(host="localhost", port=1883, keepalive=60)
mqtt = FastMQTT(config=mqtt_config)

CONTROLLER_TOPIC = "00:70:07:24:26:D0/alarm/commands"
sensors_cache = {}
device_state = SystemState()


async def send_mqtt_command(cmd: str, action: str, sensor_id: Optional[int] = None, **kwargs):
    """Send command to mqtt with optional arbitrary parameters"""
    payload = {"cmd": cmd, "action": action}

    if sensor_id is not None:
        payload["id"] = sensor_id

    payload.update(kwargs)

    print(f"🚀 ВІДПРАВЛЯЮ В MQTT: {json.dumps(payload)}")

    mqtt.publish(CONTROLLER_TOPIC, json.dumps(payload))
