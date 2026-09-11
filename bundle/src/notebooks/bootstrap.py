# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 Agents in a Day — one-click bootstrap
# MAGIC
# MAGIC Run all cells on **serverless notebook compute**. Setup runs sequentially in
# MAGIC this notebook's Spark session: maintenance tables, sales tables, the metric
# MAGIC view, Sales Genie, dashboard, and parsed fault reports. No setup job or
# MAGIC Lakeflow pipeline is deployed or started, and no CLI installation is needed.
# MAGIC
# MAGIC The SQL warehouse is only linked to Genie and the dashboard for later use.
# MAGIC Lab 3's Lakebase project is created by each participant during Lab 3.

# COMMAND ----------

dbutils.widgets.text("catalog", "sunny_bay_roastery")
dbutils.widgets.text("warehouse_id", "")
catalog = dbutils.widgets.get("catalog").strip()
if not catalog or not all(c.isalnum() or c == "_" for c in catalog):
    raise ValueError("Set catalog to a name containing only letters, numbers, and underscores.")

# COMMAND ----------

# MAGIC %md ## 1. Check configuration and create the catalog

# COMMAND ----------

from pathlib import Path
from databricks.sdk import WorkspaceClient

# All %run notebooks are siblings, so their relative data/dashboard paths work too.
bundle_root = str(Path.cwd().parent.parent)
if not (Path(bundle_root) / "databricks.yml").is_file():
    raise RuntimeError("Run bootstrap from bundle/src/notebooks inside the cloned Git Folder.")

w = WorkspaceClient()
warehouse_id = dbutils.widgets.get("warehouse_id").strip()
if not warehouse_id:
    matches = [wh.id for wh in w.warehouses.list()
               if wh.name == "Serverless Starter Warehouse"]
    if len(matches) != 1:
        raise ValueError("Set warehouse_id to a SQL warehouse you can use for Genie and the dashboard.")
    warehouse_id = matches[0]
else:
    w.warehouses.get(warehouse_id)

# Create the catalog before any of the included notebooks writes to it.
# CREATE CATALOG works on Free Edition (SQL path); if creation is restricted (locked-down
# workspace where an admin pre-provisions catalogs), fall back to USE. Only fail if the
# catalog can neither be created nor accessed.
try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
    print(f"✅ Catalog ready (created or already existed): {catalog}")
except Exception as create_err:
    try:
        spark.sql(f"USE CATALOG `{catalog}`")
        print(f"✅ Catalog `{catalog}` already exists and is usable "
              f"(creation was restricted, using the existing one).")
    except Exception as use_err:
        raise RuntimeError(
            f"Cannot create or access catalog `{catalog}`.\n"
            f"  - creation failed: {create_err}\n"
            f"  - access failed:   {use_err}\n"
            "Ask an admin to create it (or grant you CREATE CATALOG), or set the "
            "'catalog' widget to a catalog you can write to."
        ) from use_err

# Before writing anything, reject tables owned by the older Lakeflow setup.
# They cannot be replaced by ordinary Delta writes. Leave them intact.
legacy_tables = spark.sql(f"""
    SELECT table_schema, table_name FROM `{catalog}`.information_schema.tables
    WHERE table_schema IN ('silver', 'gold', 'coffee_maintenance')
      AND table_type IN ('STREAMING_TABLE', 'MATERIALIZED_VIEW')
""").collect()
if legacy_tables:
    raise RuntimeError(
        "This catalog contains tables managed by the previous pipeline setup. "
        "Choose a new catalog in the catalog widget and Run All. Existing data is preserved. "
        f"Pipeline tables: {[r.table_schema + '.' + r.table_name for r in legacy_tables]}"
    )

# %run shares Python state. Keep explicit parameters separate from child widgets,
# whose defaults are used by Databricks when running an included notebook.
_bootstrap_parameters = {"catalog": catalog, "gold_schema": "gold",
                         "warehouse_id": warehouse_id, "prefix": ""}

# COMMAND ----------

# MAGIC %md ## 2. Install the Genie Code skills

# COMMAND ----------

# Non-fatal: if this can't write, the labs tell you how to add the skills by hand.
import pathlib
import shutil

_user = spark.sql("SELECT current_user()").first()[0]
_skills = ["dispatch-plan", "add-lakebase-short-term-memory"]
for _skill in _skills:
    _src = pathlib.Path(bundle_root).parent / "app" / ".claude" / "skills" / _skill / "SKILL.md"
    _dst = pathlib.Path(f"/Workspace/Users/{_user}/.assistant/skills/{_skill}")
    try:
        _dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(_src, _dst / "SKILL.md")
        print(f"✅ Installed Genie Code skill '{_skill}' at {_dst}")
    except Exception as e:
        print(f"⚠️  Could not install the Genie Code skill '{_skill}': {e}\n"
              f"    Open Genie Code → Settings → 'Open skills folder' and copy "
              f"app/.claude/skills/{_skill}/SKILL.md into it manually.")

# COMMAND ----------

# MAGIC %md ## 3. Create the maintenance tables and copy the fault report PDFs

# COMMAND ----------

# MAGIC %run "./Lab 0 - Setup"

# COMMAND ----------

# MAGIC %md ## 4. Generate sales data and build the silver and gold tables

# COMMAND ----------

# MAGIC %run ./generate_data

# COMMAND ----------

# MAGIC %run ./build_sales_tables

# COMMAND ----------

# MAGIC %md ## 5. Create the metric view, Sales Genie, and dashboard

# COMMAND ----------

# MAGIC %run ./deploy_metric_view

# COMMAND ----------

# MAGIC %run ./deploy_genie_space

# COMMAND ----------

# MAGIC %run ./deploy_dashboard

# COMMAND ----------

# MAGIC %md ## 6. Parse and extract the fault reports
# MAGIC This batch reads all workshop PDFs and replaces the two output tables.
# MAGIC To process added or changed PDFs later, run `build_fault_reports` again.

# COMMAND ----------

# MAGIC %run ./build_fault_reports

# COMMAND ----------

print(f"🎉 All set. Everything is in catalog `{catalog}`. Head to Lab 1.")
