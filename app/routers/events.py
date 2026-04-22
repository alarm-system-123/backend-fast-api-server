"""Get api routes"""
from fastapi import APIRouter
from app.database import events_collection

router = APIRouter(prefix="/events", tags=["Events History"])

@router.get("/{device_id}")
async def get_events(device_id: str):
    """Get all events for a device"""
    cursor = events_collection.find({"device_id": device_id}).sort("timestamp", -1).limit(250)
    events = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        events.append(doc)
    return events
