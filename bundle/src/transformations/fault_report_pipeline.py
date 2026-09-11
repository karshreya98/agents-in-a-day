# Databricks notebook source
# MAGIC %md
# MAGIC # Fault Report Pipeline (Spark Declarative Pipeline)
# MAGIC
# MAGIC This pipeline:
# MAGIC 1. Reads new PDF files from the `fault_reports` UC Volume as a streaming table
# MAGIC    and turns each one into text with `ai_parse_document()`.
# MAGIC 2. Extracts structured fields using `ai_extract()`.
# MAGIC 3. Writes the results to `fault_reports_structured`.
# MAGIC
# MAGIC Attach this file to the **Agents in a Day SDP** pipeline defined in
# MAGIC `bundle/resources/pipeline.yml`. New fault reports dropped into the Volume
# MAGIC are picked up automatically on the next pipeline run.

# COMMAND ----------

from pyspark import pipelines as dp
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))
from fault_report_transforms import parse_reports, extract_reports

CATALOG = spark.conf.get("pipeline.catalog", "sunny_bay_roastery")
SCHEMA  = spark.conf.get("pipeline.target_schema", "coffee_maintenance")
VOLUME  = spark.conf.get("pipeline.volume_path",
                         f"/Volumes/{CATALOG}/{SCHEMA}/fault_reports/")

# ── Bronze: raw text files ───────────────────────────────────────────────────

@dp.table(
    name="fault_reports_raw",
    comment="Raw text parsed from fault report PDFs in the UC Volume (streaming, auto-loader)",
    table_properties={"quality": "bronze"},
)
def fault_reports_raw():
    files = (spark.readStream.format("cloudFiles")
             .option("cloudFiles.format", "binaryFile")
             .option("pathGlobFilter", "*.pdf")
             .option("cloudFiles.schemaLocation", f"{VOLUME}/_schema")
             .load(VOLUME))
    return parse_reports(files)


@dp.table(
    name="fault_reports_structured",
    comment="Structured fault report fields extracted by ai_extract",
    table_properties={"quality": "gold"},
)
def fault_reports_structured():
    return extract_reports(spark.readStream.table("fault_reports_raw"))
