from pydantic import BaseModel

class MQTTCommand(BaseModel):
    """How to parse mqtt commands"""
    cmd: str
    action: str
