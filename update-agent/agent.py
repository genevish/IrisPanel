#!/usr/bin/env python3
"""IrisPanel update agent — polls for new releases and applies them."""

import hashlib
import json
import logging
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import httpx

CONFIG_PATH = Path.home() / ".iris_updater_config.json"

log = logging.getLogger("iris-updater")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        log.error("Config not found at %s", CONFIG_PATH)
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict):
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def check_latest(server_url: str) -> dict | None:
    try:
        resp = httpx.get(f"{server_url}/api/latest", timeout=15)
        if resp.status_code == 404:
            log.info("No releases available on server")
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception:
        log.exception("Failed to check for updates")
        return None


def download_release(server_url: str, version: int, dest: Path) -> bool:
    try:
        with httpx.stream("GET", f"{server_url}/api/download/{version}", timeout=120) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception:
        log.exception("Failed to download release %d", version)
        return False


def apply_update(tarball: Path, version: int, config: dict) -> bool:
    install_dir = Path(config["install_dir"])
    backup_dir = install_dir.parent / (install_dir.name + ".prev")
    service_name = config["service_name"]
    extract_dir = Path(f"/tmp/irispanel-{version}")

    # Clean up any previous failed extraction
    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    try:
        # Extract tarball
        log.info("Extracting %s", tarball.name)
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(path=extract_dir)

        extracted_app = extract_dir / "irispanel"
        if not extracted_app.exists():
            log.error("Tarball missing irispanel/ directory")
            return False

        # Stop service
        log.info("Stopping %s", service_name)
        subprocess.run(
            ["sudo", "systemctl", "stop", service_name],
            check=True, timeout=30,
        )

        # Backup current install
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        if install_dir.exists():
            log.info("Backing up %s -> %s", install_dir, backup_dir)
            shutil.move(str(install_dir), str(backup_dir))

        # Move new version into place
        log.info("Installing new version")
        shutil.move(str(extracted_app), str(install_dir))

        # Copy venv from backup
        venv_backup = backup_dir / "venv"
        venv_dest = install_dir / "venv"
        if venv_backup.exists():
            log.info("Restoring venv")
            shutil.copytree(str(venv_backup), str(venv_dest), symlinks=True)

        # Install requirements
        pip_path = venv_dest / "bin" / "pip"
        req_path = install_dir / "requirements.txt"
        if pip_path.exists() and req_path.exists():
            log.info("Installing requirements")
            subprocess.run(
                [str(pip_path), "install", "-r", str(req_path)],
                check=True, timeout=120,
            )

        # Start service
        log.info("Starting %s", service_name)
        subprocess.run(
            ["sudo", "systemctl", "start", service_name],
            check=True, timeout=30,
        )

        # Health check
        time.sleep(5)
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True,
        )
        if result.stdout.strip() != "active":
            log.error("Service failed to start after update")
            rollback(install_dir, backup_dir, service_name)
            return False

        log.info("Update to version %d successful", version)
        return True

    except Exception:
        log.exception("Update failed, rolling back")
        rollback(install_dir, backup_dir, service_name)
        return False
    finally:
        # Clean up extraction dir
        if extract_dir.exists():
            shutil.rmtree(extract_dir)


def rollback(install_dir: Path, backup_dir: Path, service_name: str):
    try:
        log.info("Rolling back to previous version")
        if install_dir.exists():
            shutil.rmtree(install_dir)
        if backup_dir.exists():
            shutil.move(str(backup_dir), str(install_dir))
        subprocess.run(
            ["sudo", "systemctl", "start", service_name],
            check=True, timeout=30,
        )
        log.info("Rollback complete")
    except Exception:
        log.exception("Rollback failed! Manual intervention required")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config = load_config()
    server_url = config["server_url"].rstrip("/")
    poll_interval = config.get("poll_interval", 60)
    current_version = config.get("current_version", 0)

    log.info("IrisPanel Update Agent started")
    log.info("Server: %s | Poll: %ds | Current version: %d",
             server_url, poll_interval, current_version)

    while True:
        release = check_latest(server_url)

        if release and release["version"] > current_version:
            version = release["version"]
            log.info("New version available: %d (current: %d)", version, current_version)

            tarball = Path(f"/tmp/irispanel-{version}.tar.gz")
            if not download_release(server_url, version, tarball):
                time.sleep(poll_interval)
                continue

            # Verify checksum
            actual_sha = compute_sha256(tarball)
            if actual_sha != release["sha256"]:
                log.error("SHA-256 mismatch! Expected %s, got %s",
                          release["sha256"], actual_sha)
                tarball.unlink(missing_ok=True)
                time.sleep(poll_interval)
                continue

            log.info("Checksum verified, applying update")
            if apply_update(tarball, version, config):
                current_version = version
                config["current_version"] = current_version
                save_config(config)
            else:
                log.error("Update to version %d failed", version)

            tarball.unlink(missing_ok=True)

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
