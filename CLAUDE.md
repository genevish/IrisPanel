# The Iris Panel

Philips Hue smart light control app with a FastAPI backend and React frontend (CDN-loaded, no build step).

## Tech Stack

- **Backend**: Python 3, FastAPI, uvicorn, phue (Philips Hue SDK), httpx
- **Frontend**: React 18 + htm (tagged template literals via CDN import maps), Tailwind CSS (CDN play mode)
- **Config**: `~/.irispanel_config.json` (persists bridge IP)
- **Web port**: 5050

## File Structure

```
backend/
  __init__.py
  main.py            # FastAPI app, CORS, router includes, static serving
  bridge.py           # HueBridgeConnection class (wraps phue + config)
  models.py           # Pydantic request/response models
  routes/
    __init__.py
    connection.py     # GET /api/status, POST /api/connect
    lights.py         # GET /api/lights, PUT /api/lights/{id}
    groups.py         # GET/POST /api/groups, PUT/DELETE /api/groups/{id}, GET /api/room-classes
frontend/
  index.html          # Entry point with import maps (React/htm via CDN) + Tailwind + kiosk drag-scroll
  static/
    app.js            # React root renderer
    lib.js            # htm + React binding (exports html)
    api.js            # Fetch wrapper
    state.js          # BridgeContext provider + useBridge hook
    utils.js          # Color conversion (hsbToHex, hexToHsb)
    components/
      App.js
      ConnectionModal.js
      Header.js
      DeviceGrid.js
      DeviceCard.js
      LightModal.js
      GroupModal.js
run.py                # Entry point: uvicorn runner
requirements.txt      # fastapi, uvicorn[standard], phue, httpx
```

## Core Features

- Bridge auto-connect with saved IP, manual connect, link-button registration
- Individual light control: on/off, brightness (0-254), color (HSB)
- Room/group management: create, edit, delete, assign room class
- Debounced slider/color updates (150ms)
- Optimistic UI updates with rollback on failure
- 40+ predefined room types
- Kiosk mode: mouse/touch drag-scroll, text selection disabled, touch-action: manipulation
- Compact 4-column fixed grid layout (no responsive breakpoints on cards)

## Code Conventions

**Python**: snake_case functions/variables, PascalCase classes. Docstrings on modules. Pydantic models for request validation. `asyncio.to_thread()` wraps all blocking phue calls.

**JavaScript**: ES modules with import maps (no build step). camelCase functions/variables. React functional components with hooks. htm tagged template literals instead of JSX. Tailwind utility classes for styling.

## Architecture

- FastAPI app with APIRouter per domain (connection, lights, groups)
- `HueBridgeConnection` singleton manages all phue state and config persistence
- React context (`BridgeProvider` / `useBridge`) holds all client state
- Optimistic state updates: local state mutated immediately, API call fires async, rollback on error
- Debounce ref for brightness/color slider changes
- LightModal uses side-by-side layout for groups (controls left, room settings right); centered single-column for individual lights

## Running

```sh
pip install -r requirements.txt
python run.py
# Open http://localhost:5050
```

## Known Issues

1. **Broad exception catching** in bridge.py (should use specific types)
2. **No auth layer** — bridge access is IP-based only
3. **No error rollback** — failed mid-operation API calls have no recovery

## TODOs / Not Yet Implemented

- Scene/automation support
- Light effects (colorloop, strobe)
- Bridge auto-discovery (currently manual IP only)
- Multi-bridge support
- Entertainment zone support
- Light model/signature detection
