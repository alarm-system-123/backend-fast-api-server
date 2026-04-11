"""Set system on arm"""
from fastapi import APIRouter, HTTPException, status
from app.mqtt import send_mqtt_command
from app.routers.groups import groups_db

router = APIRouter(prefix="/system", tags=["System Control"])

system_state = {
    "gateway_status": "offline",
    "mode": "unknown",
    "device": "main_controller"
}


@router.get("/gateway_status")
async def get_gateway_status():
    """
    Повертає виключно статус підключення контролера до мережі/MQTT.
    """
    return {
        "device": system_state["device"],
        "gateway_status": system_state["gateway_status"]
    }


@router.get("/status")
async def get_system_status():
    """
    Повертає поточний режим роботи системи (охорона, знято тощо).
    """
    return {
        "mode": system_state["mode"],
        "gateway_status": system_state["gateway_status"]
    }


@router.post("/arm")
async def arm_system():
    """Arm system"""
    await send_mqtt_command("cmd", "arm")
    return {"status": "command_sent", "action": "arm"}

@router.post("/disarm")
async def disarm_system():
    """Disarm system"""
    await send_mqtt_command("cmd", "disarm")
    return {"status": "command_sent", "action": "disarm"}


@router.post("/partial")
async def partial_arm_system():
    """Partial arm, night schedule"""
    await send_mqtt_command("cmd", "partial")
    return {"status": "command_sent", "action": "partial"}

@router.post("/arm/group/{group_id}")
async def arm_group(group_id: int):
    """Arm a specific logical group of sensors"""

    if group_id not in groups_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Групу з ID {group_id} не знайдено."
        )

    group = groups_db[group_id]
    sensor_list = group["sensors"]

    if not sensor_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Група '{group['name']}' порожня. Додайте датчики перед постановкою на охорону."
        )

    await send_mqtt_command(
        cmd="cmd",
        action="arm_group",
        active_sensors=sensor_list
    )

    return {
        "status": "command_sent",
        "action": "arm_group",
        "group_name": group["name"],
        "active_sensors": sensor_list
    }
