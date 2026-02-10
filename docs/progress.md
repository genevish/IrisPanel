# Progress Log

## Session – 2026-02-02

### What was done
- Created `/CLAUDE.md` with full project-wide context for efficient session resumption.
- Explored entire codebase (`app.py`, `main.py`, `templates/index.html`, `static/app.js`, `static/style.css`) to gather architecture, conventions, known issues, and TODOs.

### Key decisions
- CLAUDE.md kept well under 5k token limit; no need to split into docs/.
- Sections included: project summary, tech stack, file structure, core features, code conventions, architecture, known issues, TODOs.

### Known issues documented
1. Nested `import requests` inside route handler (`app.py:187`)
2. Silent exception swallowing (`app.py:218`)
3. Broad exception catching in multiple locations
4. No auth layer
5. No error rollback for failed API calls

### Pending / Not started
- Scene/automation support
- Light effects (colorloop, strobe)
- Bridge auto-discovery
- Multi-bridge support
- Entertainment zone support
- Light model/signature detection

## Session 2 – 2026-02-02

### What was done
- Fixed room toggle not updating individual light card indicators (optimistic local state update)
- Fixed room color change not propagating to individual light cards
- Fixed yellow flash on toggle button by adding inline HSB→hex color styles in `updateCard()`
- Fixed "save room settings" not applying selected color (flush debounce, include hue/sat in payload)
- Created `refreshLightStates()` as lightweight alternative to full `loadData()` page refresh
- Replaced delayed API refetch with immediate optimistic UI updates for room toggles
- Installed `flask-cors` dependency
- Set up SSH remote for GitHub push

### Files modified
- `static/app.js` — multiple fixes to `toggleDevice()`, `handleColorChange()`, `updateCard()`, `saveRoomSettings()`, and new `refreshLightStates()` function

### Key decisions
- Optimistic local state updates preferred over refetching from bridge (faster UX)
- `updateCard()` enhanced with inline color styling rather than relying solely on CSS classes
- `refreshLightStates()` created for cases needing bridge data without full page reload

### Bugs fixed
1. Room toggle didn't update child light cards → immediate local state + `updateCard()` calls
2. Room color change didn't update child light cards → added live updates in `handleColorChange()`
3. Toggle button flashed yellow → added inline color to `updateCard()`
4. Save room settings ignored color → flush debounce timer, send hue/sat in save payload
5. Room toggle had unnecessary delay → removed timeout, use immediate optimistic update

## Session 3 – 2026-02-02 → 2026-02-09 (uncommitted)

### What was done
- **React 18 downgrade**: Import map changed from React 19 to React 18 (`esm.sh/react@18`) to fix style prop handling
- **Kiosk/touch mode**: Added mouse/touch drag-scroll IIFE in `index.html` for touchscreen kiosk use; disabled text selection and touch callout globally via CSS (`touch-action: manipulation`, `user-select: none`)
- **Compact grid layout**: `DeviceGrid.js` switched from responsive breakpoints (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`) to fixed `grid-cols-4 gap-2`; reduced outer padding/spacing
- **LightModal redesign**: Widened modal (`max-w-3xl`), side-by-side flex layout for groups (controls left, room settings right with vertical divider); individual lights get a centered narrow column (`w-64`). All spacing/sizing reduced for compact display.
- **Scroll/overflow CSS**: `html` set to `overflow: auto; height: 100%`, body uses `overflow-y: scroll` with `-webkit-overflow-scrolling: touch`, `#root` gets `overflow-y: auto`

### Files modified
- `frontend/index.html` — kiosk drag-scroll script, global touch/selection CSS, scroll overflow rules
- `frontend/static/components/DeviceGrid.js` — fixed 4-col grid, tighter spacing
- `frontend/static/components/LightModal.js` — side-by-side group layout, compact sizing

### Key decisions
- React downgraded from 19 to 18 (style prop compatibility issue)
- UI optimized for fixed-size kiosk/tablet display rather than responsive mobile-first
- Drag-scroll bypasses interactive elements (buttons, inputs, selects, links)
- Touch events registered as `{ passive: true }` for performance

## Session 4 – 2026-02-10

### What was done
- **Auto-refresh polling**: Added 3-second polling interval in `state.js` that silently refreshes light/group state from the bridge. Skips polls when a debounced slider/color update is in flight to prevent UI flicker.
- **Silent refresh mode**: `refresh()` now accepts a `silent` parameter to skip the loading spinner during background polls.
- **Debounce ref cleanup**: Fixed `debounceRef.current` not resetting to `null` after timeout fires, which would permanently block polling.
- **No-cache middleware**: Added `NoCacheStaticMiddleware` to `backend/main.py` — sets `Cache-Control: no-cache` on all `/static/` paths so browsers always fetch fresh JS.
- **Color-aware accent bars**: Updated `DeviceCard.js` top and bottom accent bars to use the light's actual HSB color (`glowColor`) instead of a fixed purple/indigo gradient. Falls back to the gradient when no color info is available.
- **Screen saver**: Created `ScreenSaver.js` component — dims overlay (opacity 0.7) after 1 minute idle, goes fully dark (opacity 1.0) after 5 minutes. Wakes instantly on `touchstart`, `mousedown`, or `keydown`. Dim state uses `pointer-events: none` so taps pass through; dark state uses `pointer-events: auto` to capture the wake tap.
- **Pi deployment**: Deployed to Raspberry Pi via rsync + systemd restart at `scott@192.168.0.215:~/IrisPanel/`.

### Files modified
- `frontend/static/state.js` — auto-refresh polling, silent refresh, debounce ref cleanup
- `backend/main.py` — no-cache static middleware
- `frontend/static/components/DeviceCard.js` — color-aware accent bars
- `frontend/static/components/ScreenSaver.js` — new screen saver component
- `frontend/static/components/App.js` — added ScreenSaver import and render

### Key decisions
- 3-second poll interval chosen as balance between responsiveness and API load
- Silent refresh prevents loading spinner flash during background polls
- Screen saver tracks only `touchstart`, `mousedown`, `keydown` (not `mousemove`, which caused false wakes)
- No-cache middleware applied at server level rather than per-file to ensure all static assets stay fresh

### Bugs fixed
1. Auto-refresh not working → browser serving cached `state.js` without polling code; fixed with no-cache middleware
2. Card accent bars not reflecting light color → replaced fixed gradient with dynamic `glowColor`
3. Debounce ref never clearing → added `debounceRef.current = null` after timeout fires
4. Screen saver not dimming → removed `mousemove` from tracked events