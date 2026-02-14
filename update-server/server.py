"""FastAPI update server for IrisPanel releases."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models import ReleaseInfo

STATE_FILE = Path(__file__).parent / "state.json"
RELEASES_DIR = Path(__file__).parent / "releases"

latest_release: ReleaseInfo | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global latest_release
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        if state.get("latest"):
            latest_release = ReleaseInfo(**state["latest"])
    yield


app = FastAPI(title="IrisPanel Update Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/latest")
async def get_latest():
    if latest_release is None:
        raise HTTPException(status_code=404, detail="No releases published yet")
    return latest_release


@app.get("/api/download/{version}")
async def download_release(version: int):
    tarball = RELEASES_DIR / f"irispanel-{version}.tar.gz"
    if not tarball.exists():
        raise HTTPException(status_code=404, detail=f"Release {version} not found")
    return FileResponse(
        tarball,
        media_type="application/gzip",
        filename=tarball.name,
    )
