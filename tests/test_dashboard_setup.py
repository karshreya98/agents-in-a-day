"""Regression checks for dashboard publication and custom-catalog binding."""
import json
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class DashboardSetupTests(unittest.TestCase):
    def test_create_and_update_publish_with_viewer_credentials(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                calls = []

                def request(method, path, **kwargs):
                    calls.append((method, path, kwargs))
                    if method == "GET":
                        return {"dashboards": [{
                            "display_name": "[Final] Sunny Bay Roastery - Sales Report",
                            "dashboard_id": "dashboard-123", "etag": "version-1",
                        }] if existing else []}
                    return {"dashboard_id": "dashboard-123"}

                client = SimpleNamespace(
                    current_user=SimpleNamespace(me=lambda: SimpleNamespace(user_name="test@example.com")),
                    workspace=SimpleNamespace(mkdirs=lambda _: None),
                    api_client=SimpleNamespace(do=request),
                    config=SimpleNamespace(host="https://test.example.com"),
                )
                sdk = ModuleType("databricks.sdk")
                sdk.WorkspaceClient = lambda: client
                values = {}
                widgets = SimpleNamespace(
                    text=lambda key, default: values.setdefault(key, default),
                    get=lambda key: values[key],
                )
                namespace = {
                    "dbutils": SimpleNamespace(widgets=widgets),
                    "_setup_root": ROOT / "labs/setup",
                    "_setup_parameters": {"catalog": "test_catalog", "gold_schema": "gold", "warehouse_id": "warehouse-123"},
                }
                with patch.dict(sys.modules, {"databricks.sdk": sdk}):
                    exec((ROOT / "labs/setup/notebooks/deploy_dashboard.py").read_text(), namespace)
                method, path, kwargs = calls[-1]
                self.assertEqual((method, path), ("POST", "/api/2.0/lakeview/dashboards/dashboard-123/published"))
                self.assertEqual(kwargs["body"], {"warehouse_id": "warehouse-123", "embed_credentials": False})
                payload = calls[-2][2]["body"]
                dataset = json.loads(payload["serialized_dashboard"])["datasets"][0]
                self.assertEqual(dataset["catalog"], "test_catalog")
                self.assertEqual(dataset["asset_name"], "test_catalog.gold.sm_fact_coffee_sales_genie")


if __name__ == "__main__":
    unittest.main()
