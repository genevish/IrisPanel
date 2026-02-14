#!/usr/bin/env python3
"""Entry point for the IrisPanel update server."""

import uvicorn

if __name__ == "__main__":
    print("Starting IrisPanel Update Server on http://localhost:5051")
    uvicorn.run("server:app", host="0.0.0.0", port=5051, reload=True)
