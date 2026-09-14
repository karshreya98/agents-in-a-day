# Databricks notebook source
# MAGIC %md
# MAGIC # 🛠️ Lab 0 — Workshop Setup
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC
# MAGIC - Create the catalog, maintenance tables, and sales tables for the workshop.
# MAGIC - Prepare the Sales Genie, dashboard, and structured fault reports.
# MAGIC - Run setup on one serverless notebook compute session.
# MAGIC
# MAGIC ## Introduction
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

# MAGIC %md
# MAGIC **Step 1: Check configuration and create the catalog**
# MAGIC
# MAGIC 1. Run the following cells and wait for them to finish.

# COMMAND ----------

from pathlib import Path
from databricks.sdk import WorkspaceClient

# Resolve supporting assets once; included notebooks share this path and Spark session.
repo_root = Path.cwd().parent.parent
_setup_root = repo_root / "labs" / "setup"
if not (_setup_root / "data" / "fault_reports").is_dir():
    raise RuntimeError(
        "Open labs/notebooks/Lab 0 - Setup inside the cloned Git Folder. "
        "The notebook needs the supporting files in labs/setup."
    )

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
_setup_parameters = {"catalog": catalog, "gold_schema": "gold",
                         "warehouse_id": warehouse_id, "prefix": ""}

# COMMAND ----------

# MAGIC %md
# MAGIC **Step 2: Install the Genie Code skills**
# MAGIC
# MAGIC 1. Run the following cells and wait for them to finish.

# COMMAND ----------

# Non-fatal: if this can't write, the labs tell you how to add the skills by hand.
import pathlib
import shutil

_user = spark.sql("SELECT current_user()").first()[0]
_skills = ["dispatch-plan", "add-lakebase-short-term-memory"]
for _skill in _skills:
    _src = repo_root / "app" / ".claude" / "skills" / _skill / "SKILL.md"
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

# MAGIC %md
# MAGIC **Step 3: Create the maintenance tables and copy the fault report PDFs**
# MAGIC
# MAGIC 1. Run the following cells and wait for them to finish.

# COMMAND ----------

# ── Derived names (do not edit) ─────────────────────────────────────────────
GOLD  = "gold"
MAINT = "coffee_maintenance"

print(f"catalog : {catalog}")
print(f"gold    : {catalog}.{GOLD}")
print(f"maint   : {catalog}.{MAINT}")

# COMMAND ----------
# MAGIC %md
# MAGIC **Create `coffee_maintenance` schema**

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{MAINT}`")
print(f"✅ Schema ready: {catalog}.{MAINT}")

# COMMAND ----------
# MAGIC %md
# MAGIC **Machines table (12 Sunny Bay espresso machines)**

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`machines` (
  machine_id     STRING NOT NULL,
  location_name  STRING,
  machine_model  STRING,
  manufacturer   STRING,
  install_date   DATE,
  last_service   DATE,
  status         STRING  -- 'active', 'degraded', 'offline'
)
USING DELTA
COMMENT 'Sunny Bay Roastery espresso machine registry  -  12 locations'
""")

spark.sql(f"""
INSERT OVERWRITE `{catalog}`.`{MAINT}`.`machines` VALUES
  ('CBM-001', 'Hayes Valley',       'Siemens EQ.9',       'Siemens',   '2021-03-15', '2025-11-01', 'active'),
  ('CBM-002', 'Castro',             'Nespresso Pro 600',  'Nespresso', '2020-07-22', '2025-09-15', 'active'),
  ('CBM-003', 'Mission',            'Siemens EQ.9',       'Siemens',   '2019-11-10', '2025-06-01', 'degraded'),
  ('CBM-004', 'Haight',             'DeLonghi Maestosa',  'DeLonghi',  '2022-01-05', '2026-01-20', 'active'),
  ('CBM-005', 'Nob Hill',           'Nespresso Pro 600',  'Nespresso', '2021-09-30', '2025-12-10', 'active'),
  ('CBM-006', 'SOMA',               'Siemens EQ.9',       'Siemens',   '2020-04-18', '2025-10-05', 'active'),
  ('CBM-007', 'Richmond',           'DeLonghi Maestosa',  'DeLonghi',  '2023-02-14', '2026-02-14', 'active'),
  ('CBM-008', 'Sunset',             'Nespresso Pro 600',  'Nespresso', '2021-06-01', '2025-08-22', 'active'),
  ('CBM-009', 'North Beach',        'Siemens EQ.9',       'Siemens',   '2019-08-12', '2024-12-01', 'degraded'),
  ('CBM-010', 'Tenderloin',         'DeLonghi Maestosa',  'DeLonghi',  '2022-11-30', '2026-03-01', 'active'),
  ('CBM-011', 'Pacific Heights',    'Nespresso Pro 600',  'Nespresso', '2020-12-20', '2025-07-15', 'active'),
  ('CBM-012', 'South Bay (Online)', 'Siemens EQ.9',       'Siemens',   '2021-05-10', '2025-11-30', 'active')
""")

count = spark.sql(f"SELECT count(*) as n FROM `{catalog}`.`{MAINT}`.`machines`").collect()[0]["n"]
print(f"✅ Machines: {count} rows → {catalog}.{MAINT}.machines")

# COMMAND ----------
# MAGIC %md
# MAGIC **Location managers roster**
# MAGIC
# MAGIC Marc is a **manager** over 12 location managers. His custom agent (Lab 3) maps a
# MAGIC flagged machine → its location → the manager to notify, so it can draft an addressed
# MAGIC message. Sara (from Lab 1) manages **Mission**.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`location_managers` (
  location       STRING NOT NULL,
  manager_name   STRING,
  manager_email  STRING
)
USING DELTA
COMMENT 'Location manager for each of the 12 Sunny Bay locations (Lab 3 people-coordination)'
""")

spark.sql(f"""
INSERT OVERWRITE `{catalog}`.`{MAINT}`.`location_managers` VALUES
  ('Hayes Valley',       'Priya Shah',    'priya@sunnybay.example'),
  ('Castro',             'Marcus Lin',    'marcus@sunnybay.example'),
  ('Mission',            'Sara Nguyen',   'sara@sunnybay.example'),
  ('Haight',             'Amara Okafor',  'amara@sunnybay.example'),
  ('Nob Hill',           'Ben Carter',    'ben@sunnybay.example'),
  ('SOMA',               'Wei Chen',      'wei@sunnybay.example'),
  ('Richmond',           'Tom Becker',    'tom@sunnybay.example'),
  ('Sunset',             'Nadia Farooq',  'nadia@sunnybay.example'),
  ('North Beach',        'Diego Alvarez', 'diego@sunnybay.example'),
  ('Tenderloin',         'Grace Kim',     'grace@sunnybay.example'),
  ('Pacific Heights',    'Lena Novak',    'lena@sunnybay.example'),
  ('South Bay (Online)', 'Omar Haddad',   'omar@sunnybay.example')
""")

count = spark.sql(f"SELECT count(*) as n FROM `{catalog}`.`{MAINT}`.`location_managers`").collect()[0]["n"]
print(f"✅ Location managers: {count} rows → {catalog}.{MAINT}.location_managers")

# COMMAND ----------
# MAGIC %md
# MAGIC **Fault events table (telemetry history)**

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`fault_events` (
  event_id       STRING,
  machine_id     STRING,
  event_ts       TIMESTAMP,
  fault_code     STRING,
  fault_desc     STRING,
  severity       STRING,   -- 'low', 'medium', 'high', 'critical'
  resolved       BOOLEAN,
  resolved_ts    TIMESTAMP,
  technician_id  STRING
)
USING DELTA
COMMENT 'Fault event log for all 12 Sunny Bay machines'
""")

spark.sql(f"""
INSERT OVERWRITE `{catalog}`.`{MAINT}`.`fault_events` VALUES
  ('EVT-001','CBM-003','2026-07-01 08:14:00','E-07','Pressure sensor fault',          'high',    true,  '2026-07-01 14:00:00','TECH-01'),
  ('EVT-002','CBM-003','2026-07-10 09:22:00','E-07','Pressure sensor fault',          'high',    true,  '2026-07-10 16:30:00','TECH-01'),
  ('EVT-003','CBM-003','2026-07-18 11:05:00','E-07','Pressure sensor fault  -  repeat', 'critical',false, null,                  null),
  ('EVT-004','CBM-009','2026-06-15 07:00:00','W-12','Grinder motor slow',             'medium',  true,  '2026-06-16 10:00:00','TECH-02'),
  ('EVT-005','CBM-009','2026-07-05 08:30:00','W-12','Grinder motor slow  -  repeat',    'medium',  false, null,                  null),
  ('EVT-006','CBM-002','2026-07-12 14:00:00','I-03','Routine descale overdue',        'low',     true,  '2026-07-13 09:00:00','TECH-03'),
  ('EVT-007','CBM-001','2026-06-28 06:45:00','E-11','Steam wand blockage',            'medium',  true,  '2026-06-28 12:00:00','TECH-01'),
  ('EVT-008','CBM-006','2026-07-20 10:10:00','E-07','Pressure sensor fault',          'high',    false, null,                  null),
  ('EVT-009','CBM-004','2026-07-14 07:30:00','T-05','Boiler temperature instability', 'medium',  false, null,                  null),
  ('EVT-010','CBM-007','2026-07-16 08:05:00','M-08','Milk system underperformance',   'medium',  false, null,                  null),
  ('EVT-011','CBM-011','2026-07-09 06:00:00','I-03','Scale buildup - flow decline',   'low',     false, null,                  null),
  ('EVT-012','CBM-012','2026-07-11 03:20:00','C-01','Connectivity dropout',           'low',     true,  '2026-07-11 09:00:00','TECH-02')
""")

count = spark.sql(f"SELECT count(*) as n FROM `{catalog}`.`{MAINT}`.`fault_events`").collect()[0]["n"]
print(f"✅ Fault events: {count} rows → {catalog}.{MAINT}.fault_events")

# COMMAND ----------
# MAGIC %md
# MAGIC **Service orders table (Lab 3 write-back target)**

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`service_orders` (
  order_id          STRING,
  machine_id        STRING,
  created_ts        TIMESTAMP,
  fault_code        STRING,
  part_id           STRING,
  technician_notes  STRING,
  status            STRING   -- 'pending', 'dispatched', 'completed'
)
USING DELTA
COMMENT 'Service orders created by Marc via the custom agent  -  populated in Lab 3'
""")

print(f"✅ Service orders table ready (empty  -  Lab 3 populates it)")
print(f"   → {catalog}.{MAINT}.service_orders")

# COMMAND ----------
# MAGIC %md
# MAGIC **Fault reports Volume + upload PDFs**
# MAGIC
# MAGIC The 10 fault-report PDFs ship with this repo (`labs/setup/data/fault_reports/`)
# MAGIC and were deployed to your workspace alongside this notebook. This step just
# MAGIC copies them into the Unity Catalog Volume — no PDF generation, no extra
# MAGIC libraries, no kernel restart.

# COMMAND ----------

import os, shutil, glob

spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{MAINT}`.`fault_reports`")
VOLUME_PATH = f"/Volumes/{catalog}/{MAINT}/fault_reports"
print(f"✅ Volume ready: {VOLUME_PATH}")

SRC_DIR = str(_setup_root / "data" / "fault_reports")

pdfs = sorted(glob.glob(f"{SRC_DIR}/*.pdf"))
if not pdfs:
    raise FileNotFoundError(
        f"No fault report PDFs found in {SRC_DIR}. "
        "Check that the Git Folder includes labs/setup/data/fault_reports/*.pdf."
    )

for src in pdfs:
    name = os.path.basename(src)
    shutil.copyfile(src, f"{VOLUME_PATH}/{name}")
    print(f"  ✓ {name}  ({os.path.getsize(src):,} bytes)")

print(f"\n✅ {len(pdfs)} fault report PDFs → {VOLUME_PATH}")

# COMMAND ----------
# MAGIC %md
# MAGIC **Register `create_service_order` UC function (Lab 3)**

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION `{catalog}`.`{MAINT}`.`create_service_order`(
  machine_id       STRING COMMENT 'Machine ID, e.g. CBM-003',
  fault_code       STRING COMMENT 'Fault code, e.g. E-07',
  part_id          STRING COMMENT 'Part to order, e.g. SIE-EQ9-PUMP-003',
  technician_notes STRING COMMENT 'Free-text notes for the technician'
)
RETURNS STRING
COMMENT 'Creates a service order and returns the new order ID. Used by Marc\\'s custom agent in Lab 3.'
LANGUAGE PYTHON
AS $$
import random
order_id = f"SO-{{random.randint(10000, 99999)}}"
try:
    import requests, os
    host  = os.environ.get("DATABRICKS_HOST", "")
    token = os.environ.get("DATABRICKS_TOKEN", "")
    if host and token:
        sql = (
            f"INSERT INTO `{catalog}`.`{MAINT}`.`service_orders` "
            "(order_id, machine_id, created_ts, fault_code, part_id, technician_notes, status) VALUES "
            f"('{{order_id}}', '{{machine_id}}', current_timestamp(), '{{fault_code}}', '{{part_id}}', '{{technician_notes}}', 'pending')"
        )
        requests.post(
            f"{{host}}/api/2.0/sql/statements",
            headers={{"Authorization": f"Bearer {{token}}", "Content-Type": "application/json"}},
            json={{"statement": sql, "wait_timeout": "10s"}},
            timeout=15,
        )
except Exception:
    pass
return order_id
$$
""")

print(f"✅ UC function registered: {catalog}.{MAINT}.create_service_order")

# COMMAND ----------

# MAGIC %md
# MAGIC **Step 4: Generate sales data and build the silver and gold tables**
# MAGIC
# MAGIC 1. Run the following cells and wait for them to finish.

# COMMAND ----------

# MAGIC %run ../setup/notebooks/generate_data

# COMMAND ----------

# MAGIC %run ../setup/notebooks/build_sales_tables

# COMMAND ----------

# MAGIC %md
# MAGIC **Step 5: Create the metric view, Sales Genie, and dashboard**
# MAGIC
# MAGIC 1. Run the following cells and wait for them to finish.

# COMMAND ----------

# MAGIC %run ../setup/notebooks/deploy_metric_view

# COMMAND ----------

# MAGIC %run ../setup/notebooks/deploy_genie_space

# COMMAND ----------

# MAGIC %run ../setup/notebooks/deploy_dashboard

# COMMAND ----------

# MAGIC %md
# MAGIC **Step 6: Parse and extract the fault reports**
# MAGIC
# MAGIC 1. Run the following cells and wait for them to finish.
# MAGIC
# MAGIC This batch reads all workshop PDFs and replaces the two output tables.
# MAGIC To process added or changed PDFs later, run `build_fault_reports` again.

# COMMAND ----------

# MAGIC %run ../setup/notebooks/build_fault_reports

# COMMAND ----------

# MAGIC %md
# MAGIC ## What Happens Next
# MAGIC
# MAGIC Setup is complete. Open Lab 1 to start working with the Genie agents.

# COMMAND ----------

print(f"🎉 All set. Everything is in catalog `{catalog}`. Head to Lab 1.")
