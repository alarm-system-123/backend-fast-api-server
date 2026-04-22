"""Sensor Router"""

from fastapi import APIRouter, HTTPException

from app.database import gateways_collection
from app.mqtt import send_mqtt_command
from app.schema.sensor_register_schema import SensorRegister

router = APIRouter(prefix="/sensors", tags=["Sensors API"])


@router.post("/{device_id}/register_new_sensor")
async def register_new_sensor(device_id: str):
    """Add new sensor (triggers pairing mode)"""
    doc = await gateways_collection.find_one({"_id": device_id})
    if not doc or doc.get("system_state", {}).get("gateway_status") != "online":
        raise HTTPException(
            status_code=503,
            detail="Системний хаб поза мережею або не знайдений."
        )

    await send_mqtt_command(
        device_id=device_id,
        cmd="sensor",
        action="add_sensor"
    )
    return {"status": "success", "action": "add_sensor"}


@router.get("/{device_id}")
async def get_sensors_by_device(device_id: str):
    """Get list of sensors for a specific hub"""
    doc = await gateways_collection.find_one({"_id": device_id})
    if doc and "sensors" in doc:
        return list(doc["sensors"].values())
    return []


@router.delete("/{device_id}/{sensor_id}")
async def remove_sensor(device_id: str, sensor_id: str):
    """Remove sensor by ID for a specific hub"""
    doc = await gateways_collection.find_one({"_id": device_id})
    if not doc or doc.get("system_state", {}).get("gateway_status") != "online":
        raise HTTPException(
            status_code=503,
            detail="Системний хаб поза мережею."
        )

    await gateways_collection.update_one(
        {"_id": device_id},
        {"$unset": {f"sensors.{sensor_id}": ""}}
    )

    await send_mqtt_command(
        device_id=device_id,
        cmd="sensor",
        action="remove_sensor",
        sensor_id=int(sensor_id)
    )

    return {"status": "success", "id": sensor_id}


@router.put("/{device_id}/{sensor_id}/config")
async def update_sensor_config(device_id: str, sensor_id: str, config: SensorRegister):
    """Update sensor settings (e.g., rename)"""
    doc = await gateways_collection.find_one({"_id": device_id})
    if not doc or doc.get("system_state", {}).get("gateway_status") != "online":
        raise HTTPException(
            status_code=503,
            detail="Системний хаб поза мережею."
        )

    await gateways_collection.update_one(
        {"_id": device_id},
        {"$set": {f"sensors.{sensor_id}.name": config.name}}
    )

    await send_mqtt_command(
        device_id=device_id,
        cmd="sensor",
        action="update_config",
        sensor_id=int(sensor_id),
        name=config.name
    )

    return {
        "status": "success",
        "action": "update_config",
        "id": sensor_id,
        "new_name": config.name
    }
