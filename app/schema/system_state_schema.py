"""System State schema"""
from pydantic import BaseModel

class SystemState(BaseModel):
    """System State class"""
    is_online: bool = False
    current_status: str = "unknown"

