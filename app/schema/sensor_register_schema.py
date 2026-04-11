"""Schema for sensor register schema"""
from pydantic import BaseModel

class SensorRegister(BaseModel):
    """Register new sensors"""
    name: str
