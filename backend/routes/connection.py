"""Connection routes."""

import asyncio
from fastapi import APIRouter, HTTPException
from phue import PhueRegistrationException

from backend.bridge import HueBridgeConnection
from backend.models import ConnectRequest

router = APIRouter()


def get_hub() -> HueBridgeConnection:
    from backend.main import hub
    return hub


@router.get("/status")
async def status():
    hub = get_hub()
    config = await asyncio.to_thread(hub.load_config)
    return {
        "connected": hub.connected,
        "bridge_ip": hub.bridge_ip,
        "saved_ip": config.get("bridge_ip"),
    }


@router.post("/connect")
async def connect(req: ConnectRequest):
    hub = get_hub()
    try:
        await asyncio.to_thread(hub.connect, req.ip)
        return {"success": True}
    except PhueRegistrationException:
        hub.bridge = None
        raise HTTPException(
            status_code=401,
            detail="Press the link button on your Hue Bridge and try again.",
        )
    except Exception as e:
        hub.bridge = None
        raise HTTPException(status_code=500, detail=str(e))
