# Session Summary – 2026-02-14 (Session 5)

## Task
Implement a complete auto-update system for IrisPanel: an update server on the developer's Mac and an update agent on the Raspberry Pi.

## What was built

### Update Server (`update-server/`)
- **`server.py`** — FastAPI app using lifespan pattern (matches `backend/main.py`). Loads `state.json` at startup. Two endpoints:
  - `GET /api/latest` → `ReleaseInfo` JSON or 404 if no releases
  - `GET /api/download/{version}` → FileResponse streaming tarball or 404
- **`publish.py`** — CLI that packages the codebase into numbered tarballs:
  1. Reads `state.json` for `next_build_number`
  2. Refuses dirty git trees (filters out `releases/` and `state.json` from check)
  3. Creates `releases/irispanel-{N}.tar.gz` with `irispanel/` prefix
  4. Computes SHA-256, updates `state.json`
  5. Cleans old releases (keeps last 5)
- **`models.py`** — `ReleaseInfo` Pydantic model (version, sha256, filename, timestamp, git_commit, size_bytes)
- **`run_server.py`** — uvicorn entry point on port 5051

### Update Agent (`update-agent/`)
- **`agent.py`** — Standalone polling script:
  1. Polls `GET /api/latest` every N seconds
  2. Downloads tarball if newer version available
  3. Verifies SHA-256 checksum
  4. Applies update: extract → stop service → backup current → move new → restore venv → pip install → start service → health check
  5. Rolls back automatically on failure (restores backup, restarts old version)
  6. Updates `current_version` in config only after success
- **`config.json.example`** — Template for `~/.iris_updater_config.json`
- **`requirements.txt`** — `httpx`
- **`iris-updater.service`** — systemd unit (user=scott, restart=always, restartSec=30)

### Other changes
- `.gitignore` — Added `update-server/releases/`, `update-server/state.json`
- `CLAUDE.md` — Added file structure, port, and usage docs for the update system

## Key design decisions
- **Integer versioning** (1, 2, 3...) — simple, auto-incrementing, no semver overhead
- **Tarball with `irispanel/` prefix** — extraction always produces a known directory name
- **SHA-256 verification** — prevents applying corrupted/tampered releases
- **Rollback on failure** — backup at `~/IrisPanel.prev/`, restored if health check fails or any exception during apply
- **Venv not in tarball** — copied back from backup, then `pip install -r requirements.txt` refreshes deps
- **Agent separate from app** — lives at `~/iris-updater/`, never overwritten by updates
- **No server hot-reload** — `state.json` read once at startup; restart server after publish
- **Sudoers for systemctl** — agent needs passwordless stop/start/restart for `irispanel` service
- **Config-based version tracking** — `current_version` in `~/.iris_updater_config.json`, only bumped after confirmed success

## Deployment steps (not yet done)
1. Deploy agent to Pi: `rsync -avz update-agent/ scott@192.168.0.215:~/iris-updater/`
2. Create config: `cp config.json.example ~/.iris_updater_config.json` (fill in server IP)
3. Install venv + deps: `python -m venv ~/iris-updater/venv && ~/iris-updater/venv/bin/pip install httpx`
4. Install systemd unit: `sudo cp iris-updater.service /etc/systemd/system/ && sudo systemctl enable --now iris-updater`
5. Add sudoers: `echo 'scott ALL=(root) NOPASSWD: /usr/bin/systemctl stop irispanel, /usr/bin/systemctl start irispanel, /usr/bin/systemctl restart irispanel' | sudo tee /etc/sudoers.d/iris-updater`

## Verification (not yet done)
1. `python update-server/publish.py` — verify tarball created
2. `python update-server/run_server.py` — hit `/api/latest`, verify response
3. Run agent locally against localhost — verify download + apply flow
4. Deploy to Pi, publish a release, watch `journalctl -u iris-updater -f`
5. Publish a broken release — verify rollback works
