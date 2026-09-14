"""Checks that notebook setup cannot accidentally launch pipeline compute."""
import ast
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs/setup"))
from batch_setup import sales_statements


class BatchSetupTests(unittest.TestCase):
    def test_all_sales_queries_are_batch_delta_with_original_projections(self):
        statements = list(sales_statements(ROOT / "labs/setup/transformations", "test_catalog"))
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
        bootstrap = ROOT / "labs/notebooks/Lab 0 - Setup.py"
        source = bootstrap.read_text()
        self.assertNotIn("run_cli", source)
        self.assertNotIn("dbutils.notebook.run", source)
        includes = [line.split('%run ', 1)[1] for line in source.splitlines() if '# MAGIC %run ' in line]
        self.assertEqual(len(includes), 6)
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
                         "_setup_parameters": expected}
            notebook = json.loads((ROOT / "labs/setup/notebooks" / (name + ".ipynb")).read_text())
            exec(''.join(notebook["cells"][0]["source"]), namespace)
            self.assertEqual(namespace["catalog"], expected["catalog"])
            if name == "deploy_genie_space":
                self.assertEqual(namespace["warehouse_id"], expected["warehouse_id"])

    def test_sales_helper_resolves_assets_from_lab0_and_standalone(self):
        helper = ROOT / "labs/setup/notebooks/build_sales_tables.py"
        setup_root = ROOT / "labs/setup"
        for included in (True, False):
            statements = []
            values = {"catalog": "test_catalog"}
            namespace = {
                "dbutils": SimpleNamespace(widgets=SimpleNamespace(
                    text=lambda key, default: values.setdefault(key, default),
                    get=lambda key: values[key],
                )),
                "spark": SimpleNamespace(sql=statements.append),
            }
            if included:
                namespace["_setup_root"] = setup_root
                namespace["_setup_parameters"] = {"catalog": "test_catalog"}
            cwd = ROOT / "labs/notebooks" if included else helper.parent
            with patch("pathlib.Path.cwd", return_value=cwd):
                exec(helper.read_text(), namespace)
            self.assertEqual(len(statements), 11)
            self.assertEqual(statements[0], "USE CATALOG `test_catalog`")
            self.assertIn("/Volumes/test_catalog/bronze/raw/dim_customer/", statements[1])
            self.assertIn("JOIN silver.dim_store", statements[-1])

    def test_lab0_contains_maintenance_setup_and_all_assets_exist(self):
        source = (ROOT / "labs/notebooks/Lab 0 - Setup.py").read_text()
        for name in ("machines", "location_managers", "fault_events", "service_orders"):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS `{{catalog}}`.`{{MAINT}}`.`{name}`", source)
        self.assertNotIn("dbutils.notebook.entry_point", source)
        self.assertFalse((ROOT / "bundle/src/notebooks/bootstrap.py").exists())
        self.assertFalse((ROOT / "bundle/databricks.yml").exists())
        self.assertEqual(len(list((ROOT / "labs/setup/data/fault_reports").glob("*.pdf"))), 10)
        self.assertTrue((ROOT / "labs/setup/dashboards/dashboard_final.lvdash.json").is_file())

    def test_notebook_python_compiles(self):
        for path in (ROOT / "labs").rglob("*.py"):
            ast.parse(path.read_text(), filename=str(path))
        for path in (ROOT / "labs/setup/notebooks").glob("*.ipynb"):
            for cell in json.loads(path.read_text())["cells"]:
                if cell["cell_type"] == "code":
                    ast.parse(''.join(cell['source']), filename=str(path))


if __name__ == '__main__':
    unittest.main()
