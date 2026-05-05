"""Set system on arm"""
from enum import Enum
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse
from app.schema.hub_shemes import RegisterHubSchema, PushTokenSchema
from app.mqtt import send_mqtt_command
from app.database import gateways_collection
from passlib.context import CryptContext

router = APIRouter(prefix="/system", tags=["System Control"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


@router.post("/{device_id}/push_token")
async def register_push_token(device_id: str, data: PushTokenSchema):
    """register push token"""
    result = await gateways_collection.update_one(
        {"_id": device_id},
        {"$addToSet": {"fcm_tokens": data.token}}
    )

    if result.matched_count == 0:
        return {"status": "error", "message": "Хаб не знайдено"}

    return {"status": "success", "message": "Токен успішно збережено"}


@router.post("/register_hub")
async def register_hub(data: RegisterHubSchema):
    """"register hub schema"""
    existing_hub = await gateways_collection.find_one({"_id": data.mac_address})

    if existing_hub:
        if verify_password(data.password, existing_hub.get("password")):
            return {"status": "success", "message": "Пристрій підключено"}

        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Неправильний пароль для цього хаба"}
        )

    hashed_password = get_password_hash(data.password)

    new_hub = {
        "_id": data.mac_address,
        "password": hashed_password,
        "system_state": {
            "gateway_status": "offline",
            "mode": "disarmed"
        },
        "sensors": {},
        "telegram_chat_ids": []
    }

    await gateways_collection.insert_one(new_hub)
    return {"status": "success", "message": "Хаб успішно зареєстровано"}
@router.get("/{device_id}/status")
async def get_full_system_status(device_id: str):
    """Return status of device """
    doc = await gateways_collection.find_one({"_id": device_id})
    if not doc:
        return {"device": "unknown", "gateway_status": "offline", "mode": "unknown"}

    system_state = doc.get("system_state", {})
    return {
        "device": system_state.get("device", "unknown"),
        "gateway_status": system_state.get("gateway_status", "offline"),
        "mode": system_state.get("mode", "unknown")
    }


class SystemAction(str, Enum):
    """Available system status"""
    # pylint: disable=invalid-name
    arm = "arm"
    disarm = "disarm"
    partial = "partial"


@router.post("/{device_id}/{action}")
async def control_system(device_id: str, action: SystemAction):
    """
    Control system status
    """
    doc = await gateways_collection.find_one({"_id": device_id})
    if not doc or doc.get("system_state", {}).get("gateway_status") != "online":
        raise HTTPException(status_code=503, detail="Системний хаб поза мережею.")

    await send_mqtt_command(device_id=device_id, cmd="cmd", action=action.value)

    return {"status": "command_sent", "action": action.value}
