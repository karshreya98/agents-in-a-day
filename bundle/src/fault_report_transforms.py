"""Shared batch/streaming fault-report projections."""

from pyspark.sql import functions as F

def parse_reports(files):
    return (
        files
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


def extract_reports(raw):
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
