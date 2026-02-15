"""Set system on arm"""
from fastapi import APIRouter

from app.mqtt import send_mqtt_command

router = APIRouter(prefix="/api", tags=["System Control"])

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
