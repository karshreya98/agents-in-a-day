"""Tools the dispatch agent composes.

A custom agent wires a *wider* palette of tools than best-effort routing exposes — two
Genie spaces, a live web MCP, **and** a Unity Catalog write-back (the guarded
`create_service_order` tool), plus plain Python. Each tool has a live path (real
Databricks calls) and a dry-run path (canned Sunny Bay data) so the app runs offline
for tests and demos.
"""
from __future__ import annotations

import json
import random
from typing import Any

from . import config

try:  # tracing is best-effort — never let its absence break a tool
    import mlflow

    _trace = mlflow.trace
except Exception:  # pragma: no cover

    def _trace(fn=None, **_kw):
        return fn if fn else (lambda f: f)


# ---------------------------------------------------------------------------
# Canned Sunny Bay data (dry-run only) — kept consistent with the workshop story.
# Locations/machines match the bootstrap `machines` table; Sara manages Mission (Lab 1).
# ---------------------------------------------------------------------------
_FLEET = [
    # machine, location, manager, unresolved_faults, fault_code, weekly_revenue
    ("CBM-003", "Mission",         "Sara Nguyen",   3, "E-07", 8200),
    ("CBM-009", "North Beach",     "Diego Alvarez", 2, "E-07", 6100),
    ("CBM-001", "Hayes Valley",    "Priya Shah",    1, "E-14", 9400),
    ("CBM-007", "Richmond",        "Tom Becker",    1, "E-02", 4300),
    ("CBM-011", "Pacific Heights", "Lena Novak",    0, None,   7200),
]

_MANAGERS = {m[1]: {"name": m[2], "email": f"{m[2].split()[0].lower()}@sunnybay.example"}
             for m in _FLEET}

# Fault code -> recommended part (feeds the create_service_order write-back).
_PARTS = {"E-07": "SIE-EQ9-PUMP-003", "E-14": "SIE-EQ9-VALVE-014", "E-02": "DEL-MAE-SEAL-002"}


def recommended_part(fault_code: str | None) -> str:
    return _PARTS.get(fault_code or "", "TBD")


class GenieTool:
    """Ask a Genie space a natural-language question."""

    def __init__(self, space_id: str, label: str):
        self.space_id = space_id
        self.label = label

    @_trace(span_type="TOOL")
    def ask(self, question: str) -> str:
        if config.DRY_RUN or not self.space_id:
            return self._canned(question)
        w = config.get_workspace_client()
        resp = w.genie.create_message_and_wait(self.space_id, question)
        parts = []
        for att in (resp.attachments or []):
            if att.text:
                parts.append(att.text.content)
            elif att.query and att.query.description:
                parts.append(att.query.description)
        return "\n".join(parts) or (resp.content or "")

    def _canned(self, question: str) -> str:
        q = question.lower()
        if "revenue" in q or "sales" in q:  # Sales Genie
            rows = [f"{m[1]}: ${m[5]:,}/wk" for m in _FLEET]
            return "Weekly revenue by store — " + "; ".join(rows)
        rows = [f"{m[0]} ({m[1]}): {m[3]} unresolved fault(s)"
                + (f", code {m[4]}" if m[4] else "") for m in _FLEET if m[3] > 0]
        return "Machines with unresolved faults — " + "; ".join(rows)


@_trace(span_type="TOOL")
def get_location_roster() -> dict[str, dict[str, str]]:
    """Map location -> {name, email} of its location manager."""
    if config.DRY_RUN:
        return _MANAGERS
    w = config.get_workspace_client()
    stmt = w.statement_execution.execute_statement(
        warehouse_id=_warehouse_id(w),
        statement=f"SELECT location, manager_name, manager_email "
                  f"FROM {config.CATALOG}.coffee_maintenance.location_managers",
    )
    roster: dict[str, dict[str, str]] = {}
    for row in (stmt.result.data_array or []) if stmt.result else []:
        roster[row[0]] = {"name": row[1], "email": row[2]}
    return roster


@_trace(span_type="TOOL")
def create_service_order(machine_id: str, fault_code: str, part_id: str,
                         technician_notes: str) -> dict[str, Any]:
    """Unity Catalog write-back: insert a row into `service_orders` with a parameterized
    `INSERT` through the SQL warehouse (`WorkspaceClient.statement_execution`). THIS is
    the accountable action — the agent gates it behind a human approval before it is
    ever called. The order ID is generated here and returned **only after** the INSERT
    reports success; a failed write raises, so the agent can never claim an order it
    didn't create."""
    if config.DRY_RUN:
        return {"order_id": f"SO-DRYRUN-{machine_id}", "status": "created",
                "machine_id": machine_id, "part_id": part_id}
    w = config.get_workspace_client()
    order_id = f"SO-{random.randint(10000, 99999)}"
    # Typed parameters (not plain dicts) — newer databricks-sdk versions require
    # parameter objects on `execute_statement`; the class was renamed along the way.
    try:
        from databricks.sdk.service.sql import StatementParameterListItem as _Param
    except ImportError:  # older SDK name
        from databricks.sdk.service.sql import StatementParameter as _Param
    stmt = w.statement_execution.execute_statement(
        warehouse_id=_warehouse_id(w),
        statement=(f"INSERT INTO {config.CATALOG}.coffee_maintenance.service_orders "
                   "(order_id, machine_id, created_ts, fault_code, part_id, "
                   "technician_notes, status) VALUES "
                   "(:order_id, :machine_id, current_timestamp(), :fault_code, "
                   ":part_id, :technician_notes, 'pending')"),
        parameters=[_Param(name="order_id", value=order_id),
                    _Param(name="machine_id", value=machine_id),
                    _Param(name="fault_code", value=fault_code),
                    _Param(name="part_id", value=part_id),
                    _Param(name="technician_notes", value=technician_notes)],
    )
    # The statement's terminal state lives at stmt.status.state (a StatementState enum).
    state = getattr(getattr(stmt, "status", None), "state", None)
    state_name = getattr(state, "value", None) or getattr(state, "name", None) or str(state)
    if state_name != "SUCCEEDED":
        err = getattr(getattr(stmt, "status", None), "error", None)
        raise RuntimeError(
            f"service-order write-back failed for {machine_id}: statement state "
            f"{state_name!r}" + (f" — {err.message}" if err else ""))
    return {"order_id": order_id, "status": "created", "machine_id": machine_id,
            "part_id": part_id}


_ROUTER_SYSTEM = (
    "You route a fleet operations manager's message to ONE action. Reply as JSON only: "
    '{"intent": "dispatch_plan|explain|approve|qa|help", "machine_id": "<CBM-xxx or empty>", '
    '"genie": "maintenance|sales", "question": "<the data question, or empty>"}. '
    "dispatch_plan = build/prioritise this week's dispatch. explain = why a machine is ranked "
    "where it is. approve = raise/approve the service order for a machine. qa = answer a data "
    "question (choose sales for revenue/store/profit, else maintenance). help = anything else."
)


@_trace(span_type="LLM")
def llm_route(message: str) -> dict[str, Any]:
    """Live intent routing via a Databricks Foundation Model (ChatDatabricks, JSON out)."""
    from databricks_langchain import ChatDatabricks

    llm = ChatDatabricks(endpoint=config.SERVING_ENDPOINT, temperature=0, max_tokens=200)
    content = llm.invoke([("system", _ROUTER_SYSTEM), ("user", message)]).content
    if "{" in content:  # tolerate models that wrap JSON in prose/fences
        content = content[content.index("{"): content.rindex("}") + 1]
    return json.loads(content)


def _warehouse_id(w) -> str:
    """First serverless SQL warehouse (matches the bootstrap default)."""
    import os

    wid = os.environ.get("WAREHOUSE_ID")
    if wid:
        return wid
    for wh in w.warehouses.list():
        return wh.id
    raise RuntimeError("No SQL warehouse found")


def parse_fleet(_answer: str) -> list[dict[str, Any]]:
    """Turn the maintenance/sales tool answers into structured rows.

    In dry-run we read the canonical `_FLEET` directly (deterministic); live agents would
    parse the Genie result. Kept separate so the graph code stays about *orchestration*.
    """
    roster = get_location_roster()
    rows = []
    for machine, location, _mgr, unresolved, code, revenue in _FLEET:
        mgr = roster.get(location, {"name": "Unknown", "email": ""})
        rows.append({
            "machine_id": machine, "location": location, "manager": mgr,
            "unresolved_faults": unresolved, "fault_code": code,
            "weekly_revenue": revenue,
        })
    return rows
