"""Pydantic models for the update server."""

from pydantic import BaseModel


class ReleaseInfo(BaseModel):
    version: int
    sha256: str
    filename: str
    timestamp: str
    git_commit: str
    size_bytes: int
