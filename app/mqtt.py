"""Send MQTT commands"""
import json
from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig(
    host="localhost",
    port=1883,
    keepalive=60
)

mqtt = FastMQTT(config=mqtt_config)

CONTROLLER_TOPIC = "00:70:07:24:26:D0/alarm/commands"

async def send_mqtt_command(cmd: str, action: str):
    """Send MQTT command"""
    payload = {"cmd": cmd, "action": action}
    mqtt.publish(CONTROLLER_TOPIC, json.dumps(payload))
