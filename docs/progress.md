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