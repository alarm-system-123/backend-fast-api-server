"""Schedule schema"""
from typing import List
from pydantic import BaseModel, Field

class ScheduleSchema(BaseModel):
    """Schedule Schema data presentation"""
    time: str = Field(..., example="23:00")
    days: List[int] = Field(..., example=[1, 2, 3, 4, 5])
    action: str = Field(..., example="arm")
    is_enabled: bool = True
