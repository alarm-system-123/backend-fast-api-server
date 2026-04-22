"""Hub schemas"""
from pydantic import BaseModel

class RegisterHubSchema(BaseModel):
    """register hub schema"""
    mac_address: str
    password: str

class PushTokenSchema(BaseModel):
    """push token schema"""
    token: str
