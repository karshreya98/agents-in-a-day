"""Render the workshop's existing sales transformations for notebook batch execution."""

import re
from pathlib import Path


def sales_statements(transformations: Path, catalog: str):
    """Keep the pipeline's projections/joins, replacing only its execution syntax.

    Dimensions are built before the fact table, silver before gold. Replacing
    Delta tables makes reruns reflect overwritten source files without duplicates.
    No materialized-view DDL is issued (that would start pipeline compute).
    """
    if not catalog or not all(c.isalnum() or c == "_" for c in catalog):
        raise ValueError("catalog must contain only letters, numbers, and underscores")
    for layer in ("silver", "gold"):
        for name in ("dim_customer", "dim_date", "dim_product", "dim_store", "fact_coffee_sales"):
            sql = (transformations / layer / f"{name}.sql").read_text()
            sql = re.sub(r"--[^\n]*", "", sql).strip()
            sql = sql.replace("${catalog}", catalog).replace("${prefix}", "")
            sql, count = re.subn(
                r"CREATE OR (?:REFRESH STREAMING TABLE|REPLACE MATERIALIZED VIEW)",
                "CREATE OR REPLACE TABLE", sql, count=1,
            )
            if count != 1:
                raise ValueError(f"Unexpected table declaration in {layer}/{name}.sql")
            sql = sql.replace("FROM STREAM read_files(", "FROM read_files(")
            # Use explicit Delta format, keeping CLUSTER BY for the fact table.
            sql = sql.replace(f"TABLE {layer}.{name}", f"TABLE {layer}.{name} USING DELTA", 1)
            yield sql
