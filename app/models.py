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

#
# # --- SENSORS ---
#
# class SensorConfig(BaseModel):
#     sensitivity: int = 50
#     led_enabled: bool = True
#
# class SensorCreate(BaseModel):
#     device_id: str = Field()
#     name: str = Field()
#     type: str = Field()
#     group_id: Optional[str] = None
#
# class SensorUpdateConfig(BaseModel):
#     config: SensorConfig
#
# class SensorResponse(SensorCreate):
#     user_id: str
#     status: str = "offline"
#     last_seen: Optional[datetime] = None
#     config: SensorConfig = SensorConfig()
#
# # --- GROUPS ---
#
# class GroupCreate(BaseModel):
#     name: str = Field()
#
# class GroupUpdateSensors(BaseModel):
#     sensor_ids: List[str]
#
# class GroupResponse(GroupCreate):
#     group_id: str
#     sensor_ids: List[str] = []
#
# # --- SCHEDULES ---
#
# class ScheduleCreate(BaseModel):
#     time: str = Field()
#     days: List[str] = Field()
#     action: str = Field() # arm / disarm
#
# # --- EVENTS ---
#
# class EventLog(BaseModel):
#     timestamp: str
#     device_id: str
#     type: str
#     message: str
