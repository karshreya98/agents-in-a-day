# Databricks notebook source
# MAGIC %md
# MAGIC # 🏗️ Setup init — ensure the catalog exists
# MAGIC
# MAGIC Runs first in the **"Agents in a Day - Setup"** job, before both the
# MAGIC maintenance (`setup`) and sales (`generate_data`) branches — each of which
# MAGIC creates its own schemas inside this catalog.
# MAGIC
# MAGIC It tries to **create** the catalog, and if creation is restricted (e.g. a
# MAGIC locked-down or Free-Edition workspace where an admin pre-provisions catalogs)
# MAGIC it falls back to **using** the existing catalog. It only fails if the catalog
# MAGIC can neither be created nor accessed — with an actionable message.

# COMMAND ----------

dbutils.widgets.text("catalog", "")
catalog = dbutils.widgets.get("catalog").strip()

if not catalog:
    raise ValueError(
        "No catalog set. Pass --var catalog=<name> to the bundle, or set the "
        '"catalog" widget when running this notebook interactively.'
    )

# COMMAND ----------

# Try to create the catalog; fall back to using an existing one if creation is
# restricted. Distinguish "created/exists" from "genuinely unavailable" so the
# error message is actionable.
try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
    print(f"✅ Catalog ready (created or already existed): {catalog}")
except Exception as create_err:
    try:
        spark.sql(f"USE CATALOG `{catalog}`")
        print(
            f"✅ Catalog `{catalog}` already exists and is usable "
            f"(creation was restricted, using the existing one)."
        )
    except Exception as use_err:
        raise RuntimeError(
            f"Cannot create or access catalog `{catalog}`.\n"
            f"  - creation failed: {create_err}\n"
            f"  - access failed:   {use_err}\n"
            "Ask an admin to create it (or grant you CREATE CATALOG), or pass "
            "--var catalog=<a catalog you can write to>."
        ) from use_err
