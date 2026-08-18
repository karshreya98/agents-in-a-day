"""FastAPI entry point for Marc's Manager Agent Databricks App.

Pattern B from the lab: the custom agent runs *inside* this app (one deploy, no
separate serving endpoint). MLflow traces are still logged to the workshop
experiment, and the Review App runs as a labeling session over those traces.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.routes import chat

app = FastAPI(title="Marc's Manager Agent")
app.include_router(chat.router, prefix="/api")

# Serve the built React frontend if present (production); dev uses Vite on :5173.
_frontend = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_frontend):
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(os.path.join(_frontend, "index.html"))
