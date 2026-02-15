"""MQTT Models"""
from typing import Optional
from pydantic import BaseModel

class MQTTCommand(BaseModel):
    """How to parse mqtt commands"""
    cmd: str
    action: str


class SensorRegister(BaseModel):
    """Register new sensors"""
    device_id: str
    name: str
    type: str
    group_id: Optional[str] = None
