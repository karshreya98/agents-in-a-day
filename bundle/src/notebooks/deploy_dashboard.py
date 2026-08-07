# Databricks notebook source
# MAGIC %md
# MAGIC # Deploy the Sunny Bay Sales dashboard
# MAGIC
# MAGIC Publishes DAID's **[Final] Sunny Bay Roastery - Sales Report** AI/BI dashboard
# MAGIC into this workspace, pointed at the metric view built by `deploy_metric_view`.
# MAGIC
# MAGIC Why this is a notebook task and not a plain DABs `dashboards:` resource: the
# MAGIC dashboard's only dataset binds to the **metric view** via `asset_name`, and DABs'
# MAGIC `dataset_catalog`/`dataset_schema` fields are **not** applied to `asset_name`
# MAGIC datasets (only to inline-SQL `queryLines`). So the asset name must be fully
# MAGIC qualified with the *runtime* catalog — which only the setup job knows. We read the
# MAGIC templated JSON, substitute `__CATALOG__`/`__GOLD_SCHEMA__`, and create/update the
# MAGIC dashboard via the Lakeview REST API (low-level `api_client.do` so it works across
# MAGIC databricks-sdk versions, matching `deploy_genie_space`).

# COMMAND ----------

dbutils.widgets.text("catalog", "sunny_bay_roastery")
catalog = dbutils.widgets.get("catalog")

dbutils.widgets.text("gold_schema", "gold")
gold_schema = dbutils.widgets.get("gold_schema")

dbutils.widgets.text("warehouse_id", "")
warehouse_id = dbutils.widgets.get("warehouse_id")

# COMMAND ----------

import json
from pathlib import Path

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

DISPLAY_NAME = "[Final] Sunny Bay Roastery - Sales Report"

# The dashboard JSON is a sibling of this notebook's folder (bundle/src/dashboards).
# generate_data.ipynb relies on the same Path.cwd() == notebook-dir behavior.
dashboard_path = (Path.cwd().parent / "dashboards" / "dashboard_final.lvdash.json").resolve()
raw = dashboard_path.read_text(encoding="utf-8")

# Substitute the catalog/schema placeholders. __PREFIX__ was already stripped when the
# file was vendored into this repo (prefix is not used here), but replace it defensively
# in case the file is ever re-copied from DAID.
serialized_dashboard = (
    raw.replace("__CATALOG__", catalog)
       .replace("__GOLD_SCHEMA__", gold_schema)
       .replace("__PREFIX__", "")
)

# Sanity check: no placeholders should remain.
leftover = [p for p in ("__CATALOG__", "__GOLD_SCHEMA__", "__PREFIX__") if p in serialized_dashboard]
if leftover:
    raise ValueError(f"Unsubstituted placeholders remain in dashboard JSON: {leftover}")

# Deploy into the running user's workspace home so it lands somewhere they can find and
# does not depend on bundle-specific paths.
me = w.current_user.me().user_name
parent_path = f"/Workspace/Users/{me}/agents-in-a-day"
w.workspace.mkdirs(parent_path)

# COMMAND ----------

# Idempotent create-or-update, found by display_name (mirrors deploy_genie_space).
def find_dashboard_by_name(display_name):
    page_token = None
    while True:
        query = {"page_size": 100}
        if page_token:
            query["page_token"] = page_token
        resp = w.api_client.do("GET", "/api/2.0/lakeview/dashboards", query=query)
        for d in (resp.get("dashboards") or []):
            if d.get("display_name") == display_name and d.get("lifecycle_state") != "TRASHED":
                return d
        page_token = resp.get("next_page_token")
        if not page_token:
            return None


existing = find_dashboard_by_name(DISPLAY_NAME)

if existing:
    dashboard_id = existing["dashboard_id"]
    w.api_client.do(
        "PATCH",
        f"/api/2.0/lakeview/dashboards/{dashboard_id}",
        body={
            "display_name": DISPLAY_NAME,
            "warehouse_id": warehouse_id,
            "serialized_dashboard": serialized_dashboard,
            "etag": existing.get("etag"),
        },
    )
    operation = "updated"
else:
    resp = w.api_client.do(
        "POST",
        "/api/2.0/lakeview/dashboards",
        body={
            "display_name": DISPLAY_NAME,
            "warehouse_id": warehouse_id,
            "serialized_dashboard": serialized_dashboard,
            "parent_path": parent_path,
        },
    )
    dashboard_id = resp.get("dashboard_id")
    operation = "created"

print(f"✅ Dashboard {operation}: {DISPLAY_NAME}")
print(f"   dashboard_id: {dashboard_id}")
print(f"   open it at: {w.config.host}/dashboardsv3/{dashboard_id}/published")
