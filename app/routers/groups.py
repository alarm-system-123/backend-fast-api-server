from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/groups", tags=["Groups API"])

groups_db = {}
group_counter = 1

class GroupCreate(BaseModel):
    name: str
    sensors: List[int] = []

class GroupUpdate(BaseModel):
    name: str | None = None
    sensors: List[int] | None = None

class GroupSensorsUpdate(BaseModel):
    sensor_ids: List[int]

@router.post("/create/group")
async def create_group(group: GroupCreate):
    """Create a new logical group of sensors"""
    global group_counter

    for existing_group in groups_db.values():
        if existing_group["name"].strip().lower() == group.name.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Група з назвою '{group.name}' вже існує!"
            )

    group_id = group_counter
    groups_db[group_id] = {
        "id": group_id,
        "name": group.name.strip(),
        "sensors": group.sensors
    }

    group_counter += 1

    return {
        "status": "success",
        "message": "Group created successfully",
        "group": groups_db[group_id]
    }

@router.get("/all/groups")
async def get_all_groups():
    """Get all groups and their assigned sensors"""
    return {
        "status": "success",
        "total": len(groups_db),
        "groups": list(groups_db.values())
    }


@router.put("/update/{group_id}/sensors")
async def add_sensors_to_group(group_id: int, data: GroupSensorsUpdate):
    """Add new sensors to an existing group"""

    # 1. Перевіряємо, чи існує така група
    if group_id not in groups_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Групу з ID {group_id} не знайдено."
        )

    group = groups_db[group_id]

    # 2. Додаємо нові датчики, перевіряючи на дублікати
    added_count = 0
    for new_sensor_id in data.sensor_ids:
        if new_sensor_id not in group["sensors"]:
            group["sensors"].append(new_sensor_id)
            added_count += 1

    # Альтернативний варіант (якщо фронтенд надсилає ПОВНИЙ новий список і хоче перезаписати старий):
    # group["sensors"] = list(set(data.sensor_ids)) # set() автоматично прибере дублікати

    return {
        "status": "success",
        "message": f"Додано {added_count} нових датчиків до '{group['name']}'",
        "group": group
    }