"""Group routes."""

import asyncio
from fastapi import APIRouter, HTTPException

from backend.bridge import ROOM_CLASSES
from backend.models import GroupUpdate, CreateGroupRequest

router = APIRouter()


def get_hub():
    from backend.main import hub
    return hub


def _require_connection():
    hub = get_hub()
    if not hub.connected:
        raise HTTPException(status_code=503, detail="Not connected")
    return hub


@router.get("/groups")
async def get_groups():
    hub = _require_connection()
    try:
        return await asyncio.to_thread(hub.get_groups)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups")
async def create_group(body: CreateGroupRequest):
    hub = _require_connection()
    if not body.lights:
        raise HTTPException(status_code=400, detail="At least one light required")
    rc = body.room_class if body.room_class in ROOM_CLASSES else "Other"
    try:
        result = await asyncio.to_thread(hub.create_group, body.name, body.lights, rc)
        return {"success": True, "group_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/groups/{group_id}")
async def update_group(group_id: int, body: GroupUpdate):
    hub = _require_connection()
    try:
        await asyncio.to_thread(
            hub.update_group, group_id,
            on=body.on, brightness=body.brightness,
            hue=body.hue, sat=body.sat,
            name=body.name, lights=body.lights,
            room_class=body.room_class,
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/groups/{group_id}")
async def delete_group(group_id: int):
    hub = _require_connection()
    try:
        await asyncio.to_thread(hub.delete_group, group_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/room-classes")
async def get_room_classes():
    return ROOM_CLASSES
