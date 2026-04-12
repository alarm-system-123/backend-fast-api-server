"""Sensor Router"""
from fastapi import APIRouter, HTTPException

from app.mqtt import send_mqtt_command, sensors_cache, device_state
from app.routers.system import system_state
from app.schema.sensor_register_schema import SensorRegister

router = APIRouter(prefix="/sensors", tags=["Sensors API"])


@router.post("/register_new_sensor")
async def register_new_sensor():
    """Add new sensor (triggers pairing mode)"""
    if system_state.get("gateway_status") != "online":
        raise HTTPException(status_code=503, detail="Системний хаб поза мережею.")

    await send_mqtt_command("sensor", "add_sensor")
    return {"status": "success", "action": "add_sensor"}


@router.delete("/{sensor_id}")
async def remove_sensor(sensor_id: int):
    """Remove sensor by ID"""
    if system_state.get("gateway_status") != "online":
        raise HTTPException(status_code=503, detail="Системний хаб поза мережею.")
    await send_mqtt_command("sensor", "remove_sensor", sensor_id=sensor_id)
    return {"status": "success", "action": "remove_sensor", "id": sensor_id}


@router.get("")
async def get_sensors():
    """Get list of ALL paired sensors (from ALL hubs)"""
    # Оскільки кеш тепер словник словників {mac: {id: data}},
    # нам треба зібрати всі датчики з усіх хабів в один плоский список
    all_sensors = []
    for hub_sensors in sensors_cache.values():
        all_sensors.extend(hub_sensors.values())

    return all_sensors


# ІДЕАЛЬНИЙ ВАРІАНТ НА МАЙБУТНЄ:
# Створити новий ендпоінт, який просить датчики конкретного хаба:
@router.get("/{device_id}")
async def get_sensors_by_device(device_id: str):
    if device_id in sensors_cache:
        return list(sensors_cache[device_id].values())
    return []

@router.put("/{sensor_id}/config")
async def update_sensor_config(sensor_id: int, config: SensorRegister):
    """Update sensor settings (e.g., rename)"""
    if system_state.get("gateway_status") != "online":
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
