# Databricks notebook source
# MAGIC %md
# MAGIC # Parse fault reports on this notebook's compute
# MAGIC Run after maintenance setup. Rerunning replaces the output with all current PDFs.

# COMMAND ----------

from pathlib import Path
import sys

sys.path.insert(0, str(globals().get("_setup_root", Path.cwd().parent)))
from fault_report_transforms import parse_reports, extract_reports

dbutils.widgets.text("catalog", "sunny_bay_roastery")
catalog = globals().get("_setup_parameters", {}).get(
    "catalog", dbutils.widgets.get("catalog")
)
report_schema = f"`{catalog}`.coffee_maintenance"
files = (spark.read.format("binaryFile").option("pathGlobFilter", "*.pdf")
         .load(f"/Volumes/{catalog}/coffee_maintenance/fault_reports/"))
# Persist parsing before extraction so downstream actions don't parse the PDFs again.
parse_reports(files).write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{report_schema}.fault_reports_raw")
raw = spark.table(f"{report_schema}.fault_reports_raw")
if raw.filter("raw_text IS NULL OR trim(raw_text) = ''").limit(1).count():
    raise RuntimeError("Some PDFs could not be parsed. Inspect fault_reports_raw and rerun this notebook.")
extract_reports(raw).write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{report_schema}.fault_reports_structured")
print(f"✅ Fault report tables ready in {catalog}.coffee_maintenance")
