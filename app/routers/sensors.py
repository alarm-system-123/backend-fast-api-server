"""Sensor Router"""
from fastapi import APIRouter
from app.mqtt import send_mqtt_command, sensors_cache

router = APIRouter(prefix="/api", tags=["Sensors API"])

@router.post("/register_new_sensor")
async def register_new_sensor():
    """Add new sensor (triggers pairing mode)"""
    await send_mqtt_command("sensor", "add_sensor")
    return {"status": "command_sent", "action": "add_sensor"}

@router.delete("/sensor/{sensor_id}")
async def remove_sensor(sensor_id: int):
    """Remove sensor by ID"""
    await send_mqtt_command("sensor", "remove_sensor", sensor_id=sensor_id)
    return {"status": "command_sent", "action": "remove_sensor", "id": sensor_id}


@router.get("/sensors/status")
async def get_sensor_status():
    """Get status of all paired sensors"""
    await send_mqtt_command("sensor", "sensor_status")
    return {
        "status": "success",
        "total_sensors": len(sensors_cache),
        "sensors": list(sensors_cache.values())
    }
