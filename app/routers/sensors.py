"""Sensor Router"""
from fastapi import APIRouter, HTTPException

from app.mqtt import send_mqtt_command, sensors_cache, device_state
from app.schema.sensor_register_schema import SensorRegister

router = APIRouter(prefix="/api", tags=["Sensors API"])


@router.post("/register_new_sensor")
async def register_new_sensor():
    """Add new sensor (triggers pairing mode)"""
    if not device_state.is_online:
        raise HTTPException(status_code=503, detail="Системний хаб поза мережею.")

    await send_mqtt_command("sensor", "add_sensor")
    return {"status": "success", "action": "add_sensor"}


@router.delete("/sensor/{sensor_id}")
async def remove_sensor(sensor_id: int):
    """Remove sensor by ID"""
    if not device_state.is_online:
        raise HTTPException(status_code=503, detail="Системний хаб поза мережею.")
    await send_mqtt_command("sensor", "remove_sensor", sensor_id=sensor_id)
    return {"status": "success", "action": "remove_sensor", "id": sensor_id}

@router.get("/sensors/status")
async def get_sensor_status():
    """Get status of all paired sensors"""
    await send_mqtt_command("sensor", "sensor_status")
    return {
        "status": "success",
        "total_sensors": len(sensors_cache),
        "sensors": list(sensors_cache.values())
    }

@router.put("/sensors/{sensor_id}/config")
async def update_sensor_config(sensor_id: int, config: SensorRegister):
    """Update sensor settings (e.g., rename)"""
    if not device_state.is_online:
        raise HTTPException(status_code=503, detail="Системний хаб поза мережею.")

    await send_mqtt_command(
        cmd="sensor",
        action="update_config",
        sensor_id=sensor_id,
        name=config.name
    )

    return {
        "status": "success",
        "action": "update_config",
        "id": sensor_id,
        "new_name": config.name
    }
