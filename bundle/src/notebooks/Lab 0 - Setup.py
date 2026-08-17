# Databricks notebook source
# MAGIC %md
# MAGIC # 🛠️ Agents in a Day — Setup
# MAGIC
# MAGIC This notebook builds the **maintenance** side of the workshop. It runs as one
# MAGIC task in the **"Agents in a Day - Setup"** job; sibling tasks in the same job
# MAGIC generate the **sales** star schema, the metric view, the pre-built Sales Genie,
# MAGIC and the sales dashboard. No other workshop to install first.
# MAGIC
# MAGIC This notebook creates:
# MAGIC - `coffee_maintenance` schema — `machines`, `fault_events`, `service_orders` tables
# MAGIC - Fault report PDFs in a UC Volume
# MAGIC - `create_service_order` UC function (Lab 5)
# MAGIC
# MAGIC > ✏️ **Only one thing to configure:** the `catalog` widget. Don't know which
# MAGIC > catalog to use? The first cell lists the ones you can write to.

# COMMAND ----------
# MAGIC %md
# MAGIC ## 🔍 Step 1 — Which catalog can I use?
# MAGIC
# MAGIC Run this cell to list every catalog you can write to, then set the `catalog`
# MAGIC widget at the top of the notebook to one of the ✅ names.
# MAGIC
# MAGIC *(Already know your catalog? Set the widget and skip straight to Run All.)*

# COMMAND ----------

print("Catalogs you can access:\n")
for r in spark.sql("SHOW CATALOGS").collect():
    name = r[0]
    try:
        spark.sql(f"USE CATALOG `{name}`")
        print(f"  ✅  {name}")
    except Exception:
        print(f"  ❌  {name}  (no access)")
print('\n👉 Put a ✅ name in the "catalog" widget at the top, then Run All.')

# COMMAND ----------
# MAGIC %md
# MAGIC ## ⚙️ Configuration
# MAGIC
# MAGIC When run as a job, `catalog` is passed in from `databricks.yml`. When run
# MAGIC interactively, set the `catalog` widget above (or edit the default below).

# COMMAND ----------

dbutils.widgets.text("catalog", "")  # ← set this (or pass --var catalog=... via the bundle)

catalog = dbutils.widgets.get("catalog").strip()

if not catalog:
    raise ValueError(
        "No catalog set. Run Step 1 above to see the catalogs you can write to, "
        'then type one into the "catalog" widget at the top of the notebook.'
    )

# ── Derived names (do not edit) ─────────────────────────────────────────────
GOLD  = "gold"
MAINT = "coffee_maintenance"

print(f"catalog : {catalog}")
print(f"gold    : {catalog}.{GOLD}")
print(f"maint   : {catalog}.{MAINT}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## ☕ Step 2 — Create `coffee_maintenance` schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{MAINT}`")
print(f"✅ Schema ready: {catalog}.{MAINT}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 🔧 Step 3 — Machines table (12 Sunny Bay espresso machines)

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
# MAGIC ## ⚡ Step 4 — Fault events table (telemetry history)

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
# MAGIC ## 📝 Step 5 — Service orders table (Lab 5 write-back target)

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
COMMENT 'Service orders created by Marc via the Supervisor agent  -  populated in Lab 5'
""")

print(f"✅ Service orders table ready (empty  -  Lab 5 populates it)")
print(f"   → {catalog}.{MAINT}.service_orders")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 📂 Step 6 — Fault reports Volume + upload PDFs
# MAGIC
# MAGIC The 10 fault-report PDFs ship with this repo (`bundle/src/data/fault_reports/`)
# MAGIC and were deployed to your workspace alongside this notebook. This step just
# MAGIC copies them into the Unity Catalog Volume — no PDF generation, no extra
# MAGIC libraries, no kernel restart.

# COMMAND ----------

import os, shutil, glob

spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{MAINT}`.`fault_reports`")
VOLUME_PATH = f"/Volumes/{catalog}/{MAINT}/fault_reports"
print(f"✅ Volume ready: {VOLUME_PATH}")

# Source PDFs sit next to this notebook in the deployed bundle:
#   .../src/notebooks/Lab 0 - Setup.py  ->  .../src/data/fault_reports/*.pdf
NOTEBOOK_DIR = os.path.dirname(
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
)
SRC_DIR = os.path.normpath(f"/Workspace{NOTEBOOK_DIR}/../data/fault_reports")

pdfs = sorted(glob.glob(f"{SRC_DIR}/*.pdf"))
if not pdfs:
    raise FileNotFoundError(
        f"No fault report PDFs found in {SRC_DIR}. "
        "Re-deploy the bundle so bundle/src/data/fault_reports/*.pdf is synced."
    )

for src in pdfs:
    name = os.path.basename(src)
    shutil.copyfile(src, f"{VOLUME_PATH}/{name}")
    print(f"  ✓ {name}  ({os.path.getsize(src):,} bytes)")

print(f"\n✅ {len(pdfs)} fault report PDFs → {VOLUME_PATH}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 🔩 Step 7 — Register `create_service_order` UC function (Lab 5)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION `{catalog}`.`{MAINT}`.`create_service_order`(
  machine_id       STRING COMMENT 'Machine ID, e.g. CBM-003',
  fault_code       STRING COMMENT 'Fault code, e.g. E-07',
  part_id          STRING COMMENT 'Part to order, e.g. SIE-EQ9-PUMP-003',
  technician_notes STRING COMMENT 'Free-text notes for the technician'
)
RETURNS STRING
COMMENT 'Creates a service order and returns the new order ID. Used by Marc\\'s Supervisor agent in Lab 5.'
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
# MAGIC ## ✅ Setup complete!

# COMMAND ----------

print("=" * 65)
print("✅  SETUP COMPLETE  -  you are ready for Agents in a Day!")
print("=" * 65)
print()
print("Maintenance assets (this notebook):")
print(f"  🔧 Machines      : {catalog}.{MAINT}.machines             (12 rows)")
print(f"  ⚡ Fault events  : {catalog}.{MAINT}.fault_events         (12 rows)")
print(f"  📝 Service orders: {catalog}.{MAINT}.service_orders       (empty  -  Lab 5)")
print(f"  📂 Fault reports : /Volumes/{catalog}/{MAINT}/fault_reports   (10 files)")
print(f"  🔩 UC function   : {catalog}.{MAINT}.create_service_order")
print()
print("Built by sibling tasks in the same setup job:")
print(f"  💰 Sales schema  : {catalog}.{GOLD}.fact_coffee_sales + dim_* (generate_data + sales pipeline)")
print(f"  📐 Metric view   : {catalog}.{GOLD}.sm_fact_coffee_sales_genie")
print(f"  🧞 Sales Genie   : \"Sunny Bay Sales Genie\" (over the metric view)")
print(f"  📊 Dashboard     : \"[Final] Sunny Bay Roastery - Sales Report\"")
print(f"  🗂️  fault_reports_structured : built by the Lakeflow pipeline task (used from Lab 2)")
print()
print("Next: open  labs/Lab 1  -  Sara's arc  and follow along!")
