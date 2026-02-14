#!/usr/bin/env python3
"""Publish a new IrisPanel release tarball."""

import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = Path(__file__).parent / "state.json"
RELEASES_DIR = Path(__file__).parent / "releases"

INCLUDE_PATHS = ["backend", "frontend", "run.py", "requirements.txt"]
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_DIRS = {"__pycache__"}
MAX_RELEASES = 5


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"next_build_number": 1, "latest": None}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def git_is_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    # Filter out untracked files in update-server/releases/ and state.json
    lines = [
        line for line in result.stdout.strip().splitlines()
        if line and not line.endswith("update-server/releases/")
        and "update-server/state.json" not in line
    ]
    return len(lines) == 0


def git_short_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return result.stdout.strip()


def should_exclude(path: Path) -> bool:
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    return False


def create_tarball(version: int) -> Path:
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    tarball_path = RELEASES_DIR / f"irispanel-{version}.tar.gz"

    with tarfile.open(tarball_path, "w:gz") as tar:
        for include_path in INCLUDE_PATHS:
            source = REPO_ROOT / include_path
            if source.is_file():
                arcname = f"irispanel/{include_path}"
                tar.add(source, arcname=arcname)
            elif source.is_dir():
                for file in sorted(source.rglob("*")):
                    if file.is_file() and not should_exclude(file):
                        arcname = f"irispanel/{file.relative_to(REPO_ROOT)}"
                        tar.add(file, arcname=arcname)

    return tarball_path


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def cleanup_old_releases(keep: int = MAX_RELEASES):
    tarballs = sorted(RELEASES_DIR.glob("irispanel-*.tar.gz"))
    while len(tarballs) > keep:
        old = tarballs.pop(0)
        old.unlink()
        print(f"  Removed old release: {old.name}")


def main():
    if not git_is_clean():
        print("Error: Git working tree is not clean. Commit or stash changes first.")
        sys.exit(1)

    state = load_state()
    version = state["next_build_number"]
    commit = git_short_hash()

    print(f"Publishing IrisPanel release #{version} (commit {commit})...")

    tarball = create_tarball(version)
    sha256 = compute_sha256(tarball)
    size_bytes = tarball.stat().st_size
    timestamp = datetime.now(timezone.utc).isoformat()

    state["next_build_number"] = version + 1
    state["latest"] = {
        "version": version,
        "sha256": sha256,
        "filename": tarball.name,
        "timestamp": timestamp,
        "git_commit": commit,
        "size_bytes": size_bytes,
    }
    save_state(state)

    cleanup_old_releases()

    print(f"\nRelease published successfully!")
    print(f"  Version:  {version}")
    print(f"  Commit:   {commit}")
    print(f"  File:     {tarball.name}")
    print(f"  Size:     {size_bytes:,} bytes")
    print(f"  SHA-256:  {sha256}")


if __name__ == "__main__":
    main()
