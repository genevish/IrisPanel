#!/usr/bin/env python3
"""Entry point for The Iris Panel."""

import uvicorn

if __name__ == "__main__":
    print("Starting The Iris Panel on http://localhost:5050")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5050, reload=True)
