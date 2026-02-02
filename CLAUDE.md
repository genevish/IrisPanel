# The Iris Panel

Philips Hue smart light control app with two interfaces: a Flask web UI and a tkinter desktop GUI.

## Tech Stack

- **Backend**: Python 3, Flask, flask-cors, phue (Philips Hue SDK), requests
- **Frontend**: Vanilla JS (ES6+), HTML5, CSS3 (glassmorphism, Apple Home style)
- **Desktop**: tkinter with custom Canvas-based widgets (macOS compat)
- **Config**: `~/.irispanel_config.json` (persists bridge IP)
- **Web port**: 5050

## File Structure

```
app.py            – Flask backend (REST API for bridge/lights/groups)
main.py           – Desktop GUI app (tkinter, standalone)
templates/index.html – Web UI template
static/app.js     – Web frontend logic
static/style.css  – Apple Home glassmorphism styles
```

## Core Features

- Bridge auto-connect with saved IP, manual connect, link-button registration
- Individual light control: on/off, brightness (0-254), color (HSB)
- Room/group management: create, edit, delete, assign room class
- Debounced slider/color updates (150ms)
- 40+ predefined room types

## Code Conventions

**Python**: snake_case functions/variables, PascalCase classes, underscore-prefixed private methods. Docstrings on modules/functions/classes.

**JavaScript**: camelCase functions/variables, CONSTANT_CASE for config, arrow functions, async/await for API calls.

**CSS**: BEM-inspired class naming (`.device-card`, `.card-btn`), CSS custom properties for theming, semantic state classes (`.hidden`, `.on`).

## Architecture

- Flask uses a global `bridge` singleton for Hue communication
- Web frontend uses client-side state objects (`lights`, `groups`, `roomClasses`)
- Desktop GUI uses MVC-like pattern with `HueBridgeConnection` service class
- Both interfaces share: HSB↔hex conversion, debouncing, auto-connect, light type detection

## Known Issues

1. **Nested import** in `app.py:187` — `import requests` inside route handler instead of top-level
2. **Silent exception swallowing** in `app.py:218` — `except Exception: pass` on config save
3. **Broad exception catching** in multiple locations (should use specific types)
4. **No auth layer** — bridge access is IP-based only
5. **No error rollback** — failed mid-operation API calls have no recovery

## TODOs / Not Yet Implemented

- Scene/automation support
- Light effects (colorloop, strobe)
- Bridge auto-discovery (currently manual IP only)
- Multi-bridge support
- Entertainment zone support
- Light model/signature detection
