"""FastAPI application for The Iris Panel."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.bridge import HueBridgeConnection
from backend.routes import connection, lights, groups

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

hub = HueBridgeConnection()


@asynccontextmanager
async def lifespan(app: FastAPI):
    hub.auto_connect()
    yield


app = FastAPI(title="The Iris Panel", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router, prefix="/api")
app.include_router(lights.router, prefix="/api")
app.include_router(groups.router, prefix="/api")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")
