"""Load the workshop's batch sales SQL in dependency order."""

from pathlib import Path


def sales_statements(transformations: Path, catalog: str):
    """Build silver before gold, replacing Delta tables on each setup run."""
    if not catalog or not all(c.isalnum() or c == "_" for c in catalog):
        raise ValueError("catalog must contain only letters, numbers, and underscores")
    for layer in ("silver", "gold"):
        for name in ("dim_customer", "dim_date", "dim_product", "dim_store", "fact_coffee_sales"):
            yield (transformations / layer / f"{name}.sql").read_text().replace("${catalog}", catalog)
