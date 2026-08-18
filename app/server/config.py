"""Configuration and dual-mode auth for Marc's Manager Agent app.

Runs in two environments:
- **Databricks App** (remote): uses the app's injected service-principal creds.
- **Local dev**: uses your Databricks CLI profile.

A third mode, **dry-run** (`AGENT_DRY_RUN=1`), needs no workspace at all — the tools
return canned Sunny Bay data so the agent (and this whole app) can be run and tested
offline. The workshop lab runs it live; CI / local smoke tests run it dry.
"""
from __future__ import annotations

import os
from functools import lru_cache

# --- Environment detection -------------------------------------------------
IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))
DRY_RUN = os.environ.get("AGENT_DRY_RUN", "0") == "1"

# --- Workshop wiring (set these as app resources / env vars when live) -----
CATALOG = os.environ.get("CATALOG", "sunny_bay_roastery")
MAINTENANCE_GENIE_SPACE_ID = os.environ.get("MAINTENANCE_GENIE_SPACE_ID", "")
SALES_GENIE_SPACE_ID = os.environ.get("SALES_GENIE_SPACE_ID", "")
# Serving endpoint used for drafting/synthesis (see databricks-apps skill).
SERVING_ENDPOINT = os.environ.get("SERVING_ENDPOINT", "databricks-claude-sonnet-4-5")
AI_GATEWAY_URL = os.environ.get("AI_GATEWAY_URL", "")
MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT", "/Shared/marc-manager-agent")


@lru_cache(maxsize=1)
def get_workspace_client():
    """Return an authenticated WorkspaceClient (never called in dry-run)."""
    from databricks.sdk import WorkspaceClient

    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_PROFILE", "DEFAULT")
    return WorkspaceClient(profile=profile)


def get_workspace_host() -> str:
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"
        return host
    return get_workspace_client().config.host
