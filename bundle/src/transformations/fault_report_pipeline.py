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

import dlt
from pyspark.sql import functions as F

CATALOG = spark.conf.get("pipeline.catalog", "sunny_bay_roastery")
SCHEMA  = spark.conf.get("pipeline.target_schema", "coffee_maintenance")
VOLUME  = spark.conf.get("pipeline.volume_path",
                         f"/Volumes/{CATALOG}/{SCHEMA}/fault_reports/")

# ── Bronze: raw text files ───────────────────────────────────────────────────

@dlt.table(
    name="fault_reports_raw",
    comment="Raw text parsed from fault report PDFs in the UC Volume (streaming, auto-loader)",
    table_properties={"quality": "bronze"},
)
def fault_reports_raw():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("pathGlobFilter", "*.pdf")
        .option("cloudFiles.schemaLocation", f"{VOLUME}/_schema")
        .load(VOLUME)
        .withColumn("parsed", F.expr("ai_parse_document(content)"))
        .withColumn(
            "raw_text",
            F.expr(
                """
                array_join(
                    transform(
                        try_cast(parsed:document:elements AS ARRAY<STRING>),
                        x -> from_json(x, 'STRUCT<content: STRING>').content
                    ),
                    '\n'
                )
                """
            ),
        )
        .select(
            F.col("_metadata.file_name").alias("source_file"),
            F.col("raw_text"),
            F.current_timestamp().alias("ingested_at"),
        )
    )


# ── Gold: structured extraction ──────────────────────────────────────────────

@dlt.table(
    name="fault_reports_structured",
    comment="Structured fault report fields extracted by ai_extract — source for Marc's custom agent",
    table_properties={"quality": "gold"},
)
def fault_reports_structured():
    raw = dlt.read_stream("fault_reports_raw")
    extracted = raw.withColumn(
        "fields",
        F.expr("""
            ai_extract(
                raw_text,
                array(
                    'machine_id', 'machine_model', 'fault_code',
                    'issue_description', 'location_name',
                    'contact_name', 'report_date'
                )
            )
        """),
    )
    return extracted.select(
        "source_file",
        F.col("fields.machine_id").alias("machine_id"),
        F.col("fields.machine_model").alias("machine_model"),
        F.col("fields.fault_code").alias("fault_code"),
        F.col("fields.issue_description").alias("issue_description"),
        F.col("fields.location_name").alias("location_name"),
        F.col("fields.contact_name").alias("contact_name"),
        F.col("fields.report_date").alias("report_date"),
        F.col("ingested_at").alias("extracted_at"),
    )
