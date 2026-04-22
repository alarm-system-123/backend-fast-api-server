"""Database connection and helpers"""
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.data.config import Config

MONGO_URL = f"{Config.MONGO_URL}"

client = AsyncIOMotorClient(MONGO_URL)
db = client.iot_security
gateways_collection = db.gateways
events_collection = db.events_history

async def get_system_state_for_device(device_id: str) -> dict:
    """Get system state for device"""
    doc = await gateways_collection.find_one({"_id": device_id})

    if doc and "system_state" in doc:
        return doc["system_state"]

    return {
        "gateway_status": "offline",
        "mode": "unknown",
        "device": "unknown"
    }

async def get_sensors_for_device(device_id: str) -> list:
    """Return list of sensors for device"""
    doc = await gateways_collection.find_one({"_id": device_id})

    if doc and "sensors" in doc:
        return list(doc["sensors"].values())
    return []




async def log_event(device_id: str, event_type: str, title: str, message: str):
    """
    Записує подію в історію та підтримує ліміт у 250 повідомлень на один хаб.
    event_type: 'system', 'alarm', 'info', 'warning', 'network'
    """
    event = {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "title": title,
        "message": message
    }

    await events_collection.insert_one(event)

    count = await events_collection.count_documents({"device_id": device_id})
    if count > 250:
        excess = count - 250
        oldest_docs = await (events_collection.find({"device_id": device_id}).sort("timestamp", 1).
                             limit(excess).to_list(length=excess))
        oldest_ids = [doc["_id"] for doc in oldest_docs]

        await events_collection.delete_many({"_id": {"$in": oldest_ids}})
