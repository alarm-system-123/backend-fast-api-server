"""Mqtt module"""
import json
from typing import Optional
from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig(host="localhost", port=1883, keepalive=60)
mqtt = FastMQTT(config=mqtt_config)

CONTROLLER_TOPIC = "00:70:07:24:26:D0/alarm/commands"
sensors_cache = {}


async def send_mqtt_command(cmd: str, action: str, sensor_id: Optional[int] = None):
    """Send command to mqtt"""
    payload = {"cmd": cmd, "action": action}
    if sensor_id is not None:
        payload["id"] = str(sensor_id)
    mqtt.publish(CONTROLLER_TOPIC, json.dumps(payload))
