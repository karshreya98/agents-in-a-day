# Databricks notebook source
# MAGIC %md
# MAGIC # 🛠️ Agents in a Day — Setup
# MAGIC
# MAGIC **Run this notebook after completing DAID Lab 0.**
# MAGIC
# MAGIC It creates everything Marc needs for his agent arc:
# MAGIC - `coffee_maintenance` schema
# MAGIC - `machines`, `fault_events`, `service_orders` tables
# MAGIC - Fault report files in a UC Volume
# MAGIC - `create_service_order` UC function (Lab 4)
# MAGIC
# MAGIC > ✏️ **Only one thing to configure:** set `catalog` below to match
# MAGIC > the catalog you used in DAID Lab 0.

# COMMAND ----------
# MAGIC %md
# MAGIC ## ⚡ Step 0 — Install dependencies
# MAGIC
# MAGIC **Run this cell once**, then click **Run all below** (not Run All from the top).
# MAGIC The kernel will restart automatically — that is expected.
# MAGIC
# MAGIC *(If you have already run this notebook before, skip this cell and Run All from cell 2.)*

# COMMAND ----------

%pip install fpdf2 -q

# COMMAND ----------

# ── Configuration ──────────────────────────────────────────────────────────
# When run as a job, catalog and prefix are passed in from databricks.yml.
# When run interactively, change the defaults below.

dbutils.widgets.text("catalog", "sunny_bay_roastery")  # ← change if needed
dbutils.widgets.text("prefix",  "")                    # ← optional, e.g. "sbr_"

catalog = dbutils.widgets.get("catalog")
prefix  = dbutils.widgets.get("prefix")

# ── Derived names (do not edit) ─────────────────────────────────────────────
if prefix and not prefix.endswith("_"):
    prefix += "_"

GOLD  = "gold"
MAINT = "coffee_maintenance"
P     = prefix

print(f"catalog : {catalog}")
print(f"prefix  : '{P}' (blank = none)")
print(f"gold    : {catalog}.{GOLD}")
print(f"maint   : {catalog}.{MAINT}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 🔍 Don't know which catalog to use? Run this cell first
# MAGIC
# MAGIC *(Skip this cell if you already know your catalog name)*

# COMMAND ----------

# Run this cell to list every catalog you can USE.
# Copy the name into the catalog = "..." variable above, then Run All from the top.
print("Catalogs you can access:")
print()
for r in spark.sql("SHOW CATALOGS").collect():
    name = r[0]
    try:
        spark.sql(f"USE CATALOG `{name}`")
        print(f"  ✅  {name}")
    except Exception:
        print(f"  ❌  {name}  (no access)")
print()
print('👉 Copy a ✅ name into  catalog = "..."  above, then Run All.')



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
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`{P}machines` (
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
INSERT OVERWRITE `{catalog}`.`{MAINT}`.`{P}machines` VALUES
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

count = spark.sql(f"SELECT count(*) as n FROM `{catalog}`.`{MAINT}`.`{P}machines`").collect()[0]["n"]
print(f"✅ Machines: {count} rows → {catalog}.{MAINT}.{P}machines")

# COMMAND ----------
# MAGIC %md
# MAGIC ## ⚡ Step 4 — Fault events table (telemetry history)

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`{P}fault_events` (
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
INSERT OVERWRITE `{catalog}`.`{MAINT}`.`{P}fault_events` VALUES
  ('EVT-001','CBM-003','2026-07-01 08:14:00','E-07','Pressure sensor fault',          'high',    true,  '2026-07-01 14:00:00','TECH-01'),
  ('EVT-002','CBM-003','2026-07-10 09:22:00','E-07','Pressure sensor fault',          'high',    true,  '2026-07-10 16:30:00','TECH-01'),
  ('EVT-003','CBM-003','2026-07-18 11:05:00','E-07','Pressure sensor fault  -  repeat', 'critical',false, null,                  null),
  ('EVT-004','CBM-009','2026-06-15 07:00:00','W-12','Grinder motor slow',             'medium',  true,  '2026-06-16 10:00:00','TECH-02'),
  ('EVT-005','CBM-009','2026-07-05 08:30:00','W-12','Grinder motor slow  -  repeat',    'medium',  false, null,                  null),
  ('EVT-006','CBM-002','2026-07-12 14:00:00','I-03','Routine descale overdue',        'low',     true,  '2026-07-13 09:00:00','TECH-03'),
  ('EVT-007','CBM-001','2026-06-28 06:45:00','E-11','Steam wand blockage',            'medium',  true,  '2026-06-28 12:00:00','TECH-01'),
  ('EVT-008','CBM-006','2026-07-20 10:10:00','E-07','Pressure sensor fault',          'high',    false, null,                  null)
""")

count = spark.sql(f"SELECT count(*) as n FROM `{catalog}`.`{MAINT}`.`{P}fault_events`").collect()[0]["n"]
print(f"✅ Fault events: {count} rows → {catalog}.{MAINT}.{P}fault_events")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 📝 Step 5 — Service orders table (Lab 4 write-back target)

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS `{catalog}`.`{MAINT}`.`{P}service_orders` (
  order_id          STRING,
  machine_id        STRING,
  created_ts        TIMESTAMP,
  fault_code        STRING,
  part_id           STRING,
  technician_notes  STRING,
  status            STRING   -- 'pending', 'dispatched', 'completed'
)
USING DELTA
COMMENT 'Service orders created by Marc via the Supervisor agent  -  populated in Lab 4'
""")

print(f"✅ Service orders table ready (empty  -  Lab 4 populates it)")
print(f"   → {catalog}.{MAINT}.{P}service_orders")

# COMMAND ----------
# MAGIC %md

# COMMAND ----------
# MAGIC %md
# MAGIC ## 📂 Step 6 — Fault reports Volume + generate real PDFs

# COMMAND ----------

spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{MAINT}`.`fault_reports`")
VOLUME_PATH = f"/Volumes/{catalog}/{MAINT}/fault_reports"
print(f"✅ Volume ready: {VOLUME_PATH}")

# COMMAND ----------

from fpdf import FPDF

class FaultReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, "Sunny Bay Roastery  -  Fault Report", ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def field(self, label, value):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(80, 80, 80)
        self.cell(38, 6, label, ln=False)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 6, value)

    def section(self, title):
        self.ln(3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(20, 60, 120)
        self.cell(0, 7, title, ln=True)
        self.set_text_color(20, 20, 20)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5.5, text)


REPORTS = [
    {
        "filename": "FR-2026-001.pdf",
        "meta": {
            "Report ID":   "FR-2026-001",
            "Location":    "Mission District  -  2847 Mission St",
            "Machine":     "CBM-003  |  Siemens EQ.9 Plus Connect",
            "Serial No":   "SIE-EQ9-20191110-003",
            "Date":        "2026-07-18",
            "Reported by": "Sara M. (Location Manager)",
            "Priority":    "HIGH  -  Urgent",
        },
        "fault": (
            "Fault code E-07 (Pressure Sensor Fault) has triggered three times in 18 days.\n"
            "Events on 2026-07-01, 2026-07-10, and 2026-07-18. First two resolved by TECH-01 "
            "but fault recurred each time. Machine still operational but pulling shots at "
            "7.5–8.2 bar vs normal 9.0 bar. ~20% of espresso shots rejected during fault "
            "windows. Customer complaints logged on 12 Jul and 17 Jul."
        ),
        "action": (
            "Urgent inspection required. Likely root causes: worn pump assembly or cracked "
            "pressure line. Parts anticipated: pump assembly (SIE-EQ9-PUMP-003), pressure "
            "line kit (SIE-EQ9-PL-KIT). Previous pressure transducer replacements (2 Jul, "
            "11 Jul) did not resolve the fault.\n\n"
            "Contact: sara.m@sunnybayroastery.com | +1-415-555-0103"
        ),
    },
    {
        "filename": "FR-2026-002.pdf",
        "meta": {
            "Report ID":   "FR-2026-002",
            "Location":    "North Beach  -  585 Columbus Ave",
            "Machine":     "CBM-009  |  Siemens EQ.9 Plus Connect",
            "Serial No":   "SIE-EQ9-20190812-009",
            "Date":        "2026-07-05",
            "Reported by": "James L. (Location Manager)",
            "Priority":    "MEDIUM",
        },
        "fault": (
            "Fault code W-12 (Grinder Motor Degradation). Grind time increased from normal "
            "8 seconds to 14 seconds for a double shot. First occurrence 15 Jun 2026, "
            "partially resolved, returned 5 Jul 2026. Machine is 7 years old with no major "
            "overhaul on record. Grinder burrs likely worn beyond service threshold."
        ),
        "action": (
            "Schedule grinder burr replacement and full motor inspection. No urgent production "
            "impact at this time but further degradation expected within 2–3 weeks."
        ),
    },
    {
        "filename": "FR-2026-003.pdf",
        "meta": {
            "Report ID":   "FR-2026-003",
            "Location":    "SOMA  -  199 5th St",
            "Machine":     "CBM-008  |  Nespresso Pro 600",
            "Serial No":   "NES-PRO-20210601-008",
            "Date":        "2026-07-22",
            "Reported by": "Auto-generated (telemetry alert)",
            "Priority":    "LOW  -  Preventive",
        },
        "fault": (
            "Scheduled descale notification I-03 overdue by 18 days. No active fault code. "
            "Machine operating within normal parameters. Preventive maintenance flag only."
        ),
        "action": (
            "Perform standard descale service at next available slot. Low priority  -  "
            "no production impact currently."
        ),
    },
    {
        "filename": "FR-2026-004.pdf",
        "meta": {
            "Report ID":   "FR-2026-004",
            "Location":    "Hayes Valley  -  430 Hayes St",
            "Machine":     "CBM-001  |  Siemens EQ.9 Plus Connect",
            "Serial No":   "SIE-EQ9-20210315-001",
            "Date":        "2026-06-28",
            "Reported by": "Priya K. (Location Manager)",
            "Priority":    "CLOSED  -  Resolved",
        },
        "fault": (
            "Fault code E-11 (Steam Wand Blockage). Milk steaming intermittently failing. "
            "Resolved same day by TECH-01 (manual flush). No recurrence since 28 Jun 2026."
        ),
        "action": (
            "No action required. Logged for maintenance history. Monitor for recurrence "
            "at next routine visit."
        ),
    },
    {
        "filename": "FR-2026-005.pdf",
        "meta": {
            "Report ID":   "FR-2026-005 (Supplement to FR-2026-001)",
            "Location":    "Mission District  -  2847 Mission St",
            "Machine":     "CBM-003",
            "Serial No":   "SIE-EQ9-20191110-003",
            "Date":        "2026-07-19",
            "Reported by": "TECH-01 (Field Technician)",
            "Priority":    "HIGH  -  Escalation",
        },
        "fault": (
            "Pressure readings log (last 30 days):\n"
            "  2026-06-19: 9.0 bar  -  normal\n"
            "  2026-06-25: 8.8 bar  -  slightly low\n"
            "  2026-07-01: 7.9 bar  -  E-07 triggered\n"
            "  2026-07-08: 9.1 bar  -  post-repair\n"
            "  2026-07-10: 7.8 bar  -  E-07 triggered\n"
            "  2026-07-15: 8.9 bar  -  post-repair\n"
            "  2026-07-18: 7.5 bar  -  E-07 triggered (unresolved)"
        ),
        "action": (
            "Pressure transducer replaced twice (2 Jul, 11 Jul)  -  fault persists. "
            "Pattern indicates worn pump or cracked pressure line upstream of transducer.\n\n"
            "Parts to order:\n"
            "  - Pump assembly:     SIE-EQ9-PUMP-003\n"
            "  - Pressure line kit: SIE-EQ9-PL-KIT\n\n"
            "Estimated repair time: 2 hours on-site. Escalate to senior technician."
        ),
    },
]


def make_pdf(report):
    pdf = FaultReportPDF()
    pdf.add_page()
    pdf.section("Report Details")
    for label, value in report["meta"].items():
        pdf.field(f"{label}:", value)
    pdf.section("Fault Description")
    pdf.body_text(report["fault"])
    pdf.section("Requested Action / Technician Notes")
    pdf.body_text(report["action"])
    return bytes(pdf.output())


for r in REPORTS:
    pdf_bytes = make_pdf(r)
    path = f"{VOLUME_PATH}/{r['filename']}"
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    print(f"  ✓ {r['filename']}  ({len(pdf_bytes):,} bytes)")

print(f"\n✅ {len(REPORTS)} fault report PDFs → {VOLUME_PATH}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 🔩 Step 7 — Register `create_service_order` UC function (Lab 4)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION `{catalog}`.`{MAINT}`.`create_service_order`(
  machine_id       STRING COMMENT 'Machine ID, e.g. CBM-003',
  fault_code       STRING COMMENT 'Fault code, e.g. E-07',
  part_id          STRING COMMENT 'Part to order, e.g. SIE-EQ9-PUMP-003',
  technician_notes STRING COMMENT 'Free-text notes for the technician'
)
RETURNS STRING
COMMENT 'Creates a service order and returns the new order ID. Used by Marc\\'s Supervisor agent in Lab 4.'
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
            f"INSERT INTO `{catalog}`.`{MAINT}`.`{P}service_orders` "
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

print()
print("Agents in a Day assets:")
print(f"  🔧 Machines      : {catalog}.{MAINT}.{P}machines             (12 rows)")
print(f"  ⚡ Fault events  : {catalog}.{MAINT}.{P}fault_events         (8 rows)")
print(f"  📝 Service orders: {catalog}.{MAINT}.{P}service_orders       (empty  -  Lab 4)")
print(f"  📂 Fault reports : /Volumes/{catalog}/{MAINT}/fault_reports   (5 files)")
print(f"  🔩 UC function   : {catalog}.{MAINT}.create_service_order")
print()
print("Next: open  labs/Part 1  -  Sara's arc  and follow along!")
