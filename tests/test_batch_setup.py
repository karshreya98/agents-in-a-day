"""Checks that notebook setup cannot accidentally launch pipeline compute."""
import ast
import json
import sys
import unittest
from types import SimpleNamespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bundle/src"))
from batch_setup import sales_statements


class BatchSetupTests(unittest.TestCase):
    def test_all_sales_queries_are_batch_delta_with_original_projections(self):
        statements = list(sales_statements(ROOT / "bundle/src/transformations", "test_catalog"))
        self.assertEqual(len(statements), 10)
        for sql in statements:
            self.assertIn("CREATE OR REPLACE TABLE", sql)
            self.assertIn("USING DELTA", sql)
            for forbidden in ("STREAM", "MATERIALIZED", "${"):
                self.assertNotIn(forbidden, sql)
        self.assertIn("/Volumes/test_catalog/bronze/raw/dim_customer/", statements[0])
        self.assertIn("JOIN silver.dim_product", statements[-1])
        self.assertIn("CLUSTER BY (store_key, date_key)", statements[-1])

    def test_bootstrap_includes_only_local_notebooks(self):
        bootstrap = ROOT / "bundle/src/notebooks/bootstrap.py"
        source = bootstrap.read_text()
        self.assertNotIn("run_cli", source)
        self.assertNotIn("dbutils.notebook.run", source)
        includes = [line.split('%run ', 1)[1] for line in source.splitlines() if '# MAGIC %run ' in line]
        self.assertEqual(len(includes), 7)
        for include in includes:
            name = include.strip('"').removeprefix('./')
            self.assertTrue(any((bootstrap.parent / (name + ext)).exists() for ext in ('.py', '.ipynb')))

    def test_included_notebooks_use_bootstrap_values_over_widget_defaults(self):
        expected = {"catalog": "a_different_catalog", "gold_schema": "gold",
                    "warehouse_id": "chosen_warehouse", "prefix": ""}
        for name in ("generate_data", "deploy_metric_view", "deploy_genie_space"):
            values = {}
            widgets = SimpleNamespace(
                text=lambda key, default: values.setdefault(key, default),
                get=lambda key: values[key],
            )
            namespace = {"dbutils": SimpleNamespace(widgets=widgets),
                         "_bootstrap_parameters": expected}
            notebook = json.loads((ROOT / "bundle/src/notebooks" / (name + ".ipynb")).read_text())
            exec(''.join(notebook["cells"][0]["source"]), namespace)
            self.assertEqual(namespace["catalog"], expected["catalog"])
            if name == "deploy_genie_space":
                self.assertEqual(namespace["warehouse_id"], expected["warehouse_id"])

    def test_notebook_python_compiles(self):
        for path in (ROOT / "bundle/src").rglob("*.py"):
            ast.parse(path.read_text(), filename=str(path))
        for path in (ROOT / "bundle/src/notebooks").glob("*.ipynb"):
            for cell in json.loads(path.read_text())["cells"]:
                if cell["cell_type"] == "code":
                    ast.parse(''.join(cell['source']), filename=str(path))


if __name__ == '__main__':
    unittest.main()
