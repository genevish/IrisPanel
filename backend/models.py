"""Pydantic request/response models."""

from pydantic import BaseModel


class ConnectRequest(BaseModel):
    ip: str


class LightUpdate(BaseModel):
    on: bool | None = None
    brightness: int | None = None
    hue: int | None = None
    sat: int | None = None


class GroupUpdate(BaseModel):
    on: bool | None = None
    brightness: int | None = None
    hue: int | None = None
    sat: int | None = None
    name: str | None = None
    lights: list[str] | None = None
    room_class: str | None = None


class CreateGroupRequest(BaseModel):
    name: str
    lights: list[str]
    room_class: str = "Other"
