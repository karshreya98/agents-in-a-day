"""Regression tests for the `create_service_order` write-back — the exact parameterized
INSERT, and that the order ID is returned only after a successful write."""
import os
import re
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("AGENT_DRY_RUN", "1")

from agent_server import config, tools  # noqa: E402


class _RecordingStatements:
    """Stands in for `WorkspaceClient.statement_execution`, capturing the call.

    Mirrors the SDK shape the tool reads: the terminal state at `stmt.status.state`.
    """

    def __init__(self, state="SUCCEEDED"):
        self.state = state
        self.calls = []

    def execute_statement(self, warehouse_id, statement, parameters):
        self.calls.append({"warehouse_id": warehouse_id, "statement": statement,
                           "parameters": parameters})
        return SimpleNamespace(
            status=SimpleNamespace(state=SimpleNamespace(value=self.state),
                                   error=None))


EXPECTED_INSERT = (
    "INSERT INTO test_catalog.coffee_maintenance.service_orders "
    "(order_id, machine_id, created_ts, fault_code, part_id, "
    "technician_notes, status) VALUES "
    "(:order_id, :machine_id, current_timestamp(), :fault_code, "
    ":part_id, :technician_notes, 'pending')"
)


def _live_tool(state="SUCCEEDED"):
    """The tool in live mode against a fake workspace client."""
    stmts = _RecordingStatements(state)
    client = SimpleNamespace(statement_execution=stmts)
    os.environ["WAREHOUSE_ID"] = "wh-test"

    def call():
        with patch.object(config, "DRY_RUN", False), \
             patch.object(config, "CATALOG", "test_catalog"), \
             patch.object(config, "get_workspace_client", return_value=client):
            return tools.create_service_order(
                "CBM-003", "E-07", "SIE-EQ9-PUMP-003",
                "[High] 3 unresolved fault(s) at Mission."), stmts

    return call()


def test_live_path_runs_the_exact_parameterized_insert():
    order, stmts = _live_tool()
    assert len(stmts.calls) == 1
    call = stmts.calls[0]
    assert call["warehouse_id"] == "wh-test"
    assert call["statement"] == EXPECTED_INSERT  # no string interpolation of user input
    assert [(p.name, p.value) for p in call["parameters"]] == [
        ("order_id", order["order_id"]),
        ("machine_id", "CBM-003"),
        ("fault_code", "E-07"),
        ("part_id", "SIE-EQ9-PUMP-003"),
        ("technician_notes", "[High] 3 unresolved fault(s) at Mission."),
    ]
    assert re.fullmatch(r"SO-\d{5}", order["order_id"])
    assert order["status"] == "created"
    assert order["machine_id"] == "CBM-003"


def test_failed_write_raises_and_returns_no_order():
    import pytest

    with pytest.raises(RuntimeError, match="write-back failed"):
        _live_tool(state="FAILED")


def test_dry_run_returns_canned_order():
    order = tools.create_service_order("CBM-003", "E-07", "SIE-EQ9-PUMP-003", "notes")
    assert order == {"order_id": "SO-DRYRUN-CBM-003", "status": "created",
                     "machine_id": "CBM-003", "part_id": "SIE-EQ9-PUMP-003"}
