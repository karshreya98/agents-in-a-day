# Databricks notebook source
# MAGIC %md
# MAGIC # Build sales tables on this notebook's compute
# MAGIC Read the generated files once and replace the silver and gold Delta tables.
# MAGIC The SQL files define batch Delta tables for the sales star schema.

# COMMAND ----------

from pathlib import Path
import sys

sys.path.insert(0, str(globals().get("_setup_root", Path.cwd().parent)))
from batch_setup import sales_statements

dbutils.widgets.text("catalog", "sunny_bay_roastery")
catalog = globals().get("_setup_parameters", {}).get(
    "catalog", dbutils.widgets.get("catalog")
)
spark.sql(f"USE CATALOG `{catalog}`")
for statement in sales_statements(globals().get("_setup_root", Path.cwd().parent) / "transformations", catalog):
    spark.sql(statement)
print(f"✅ Silver and gold sales tables ready in {catalog}")
