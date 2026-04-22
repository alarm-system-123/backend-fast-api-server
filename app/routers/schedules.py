""" Get all routes from schedule"""
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.database import db
from app.schema.schedule_schema import ScheduleSchema

router = APIRouter(prefix="/schedules", tags=["Schedules"])

@router.post("/{device_id}")
async def add_schedule(device_id: str, schedule: ScheduleSchema):
    """add a schedule"""
    doc = schedule.dict()
    doc["device_id"] = device_id
    result = await db.schedules.insert_one(doc)
    return {"status": "success", "id": str(result.inserted_id)}

@router.get("/{device_id}")
async def get_schedules(device_id: str):
    """get all schedules"""
    cursor = db.schedules.find({"device_id": device_id})
    schedules = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        schedules.append(doc)
    return schedules

@router.delete("/{device_id}/{schedule_id}")
async def delete_schedule(device_id: str, schedule_id: str):
    """delete a schedule"""
    result = await db.schedules.delete_one({"_id": ObjectId(schedule_id), "device_id": device_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Розклад не знайдено")
    return {"status": "success"}
