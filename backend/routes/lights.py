"""Light routes."""

import asyncio
from fastapi import APIRouter, HTTPException

from backend.models import LightUpdate

router = APIRouter()


def get_hub():
    from backend.main import hub
    return hub


def _require_connection():
    hub = get_hub()
    if not hub.connected:
        raise HTTPException(status_code=503, detail="Not connected")
    return hub


@router.get("/lights")
async def get_lights():
    hub = _require_connection()
    try:
        return await asyncio.to_thread(hub.get_lights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/lights/{light_id}")
async def update_light(light_id: int, body: LightUpdate):
    hub = _require_connection()
    try:
        await asyncio.to_thread(
            hub.update_light, light_id,
            on=body.on, brightness=body.brightness,
            hue=body.hue, sat=body.sat,
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
