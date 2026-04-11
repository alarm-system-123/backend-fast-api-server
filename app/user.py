"""User module"""
from pydantic import BaseModel
from app.schema.sensor_register_schema import SensorRegister


class User(BaseModel):
    """Show user info"""
    email: str
    username: str
    password: str
    main_controllers: list[str]
    sensors: list[SensorRegister]
