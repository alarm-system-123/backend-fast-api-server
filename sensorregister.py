"""Register new sensors"""
from typing import Optional
from pydantic import BaseModel

class SensorRegister(BaseModel):
    """Register new sensors"""
    device_id: str
    name: str
    type: str  # наприклад "motion", "door"
    group_id: Optional[str] = None
