"""Marc's dispatch agent as an explicit **LangGraph** StateGraph.

This is the honest realisation of "control flow you own": not a generic tool-calling
loop, but a graph you can read node-by-node, with a **human-in-the-loop `interrupt`** as
the approval gate before the `create_service_order` write-back.

    assess → quantify → enrich → score → assign → approval_gate ⇄ execute
                                                        (interrupt)   (write-back)

`mlflow.langchain.autolog()` traces every node automatically. A MemorySaver checkpointer
lets the graph pause at the interrupt and resume when the manager approves — the canonical
LangGraph HITL pattern. Runs fully offline (`AGENT_DRY_RUN=1`) since the nodes call the
dry-run-aware tools in `tools.py`.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from . import tools

# --- LAB 3 · TASK 2: Marc's scoring policy — deterministic, not a prompt. ---
# Try changing a value here, then re-run the plan and watch the ranking move. E.g. bump
# REVENUE_WEIGHT to 2.0 so a busy store outranks a fault-heavy quiet one.
FAULT_WEIGHT = 4.0          # points per unresolved fault
REVENUE_WEIGHT = 1.0        # points per $1,000/wk of revenue at risk
DISPATCH_THRESHOLD = 10.0   # a machine must score at least this to make the plan


class PlanState(TypedDict, total=False):
    fleet: list[dict[str, Any]]
    ranked: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    executed: list[dict[str, Any]]
    summary: str
    pending: Optional[str]


# --- Nodes -----------------------------------------------------------------
def assess(state: PlanState) -> dict:
    maintenance = tools.GenieTool(tools.config.MAINTENANCE_GENIE_SPACE_ID, "Maintenance Genie")
    answer = maintenance.ask(
        "Which machines across all locations have unresolved faults, with their fault codes?")
    return {"fleet": tools.parse_fleet_answer(answer)}


def quantify(state: PlanState) -> dict:
    sales = tools.GenieTool(tools.config.SALES_GENIE_SPACE_ID, "Sales Genie")
    sales.ask("What is the weekly coffee revenue by store?")
    fleet = state["fleet"]
    for row in fleet:
        row["revenue_at_risk"] = row["weekly_revenue"]
    return {"fleet": fleet}


def enrich(state: PlanState) -> dict:
    fleet = state["fleet"]
    for row in fleet:
        if row.get("fault_code"):  # only reach for the web when there's a code to look up
            row["bulletin"] = tools.web_search(
                f"manufacturer service bulletin for fault {row['fault_code']} espresso machine")
    return {"fleet": fleet}


def score(state: PlanState) -> dict:
    fleet = state["fleet"]
    for row in fleet:
        row["priority_score"] = round(
            FAULT_WEIGHT * row["unresolved_faults"]
            + REVENUE_WEIGHT * row["revenue_at_risk"] / 1000, 2)
    ranked = sorted(fleet, key=lambda r: r["priority_score"], reverse=True)
    return {"ranked": ranked}


def assign(state: PlanState) -> dict:
    actions = []
    for row in state["ranked"]:
        # A machine is worth dispatching only if it actually has faults and scores high.
        if row["unresolved_faults"] == 0 or row["priority_score"] < DISPATCH_THRESHOLD:
            continue
        row["draft_message"] = _draft_message(row)
        row["needs_approval"] = True
        actions.append(row)
    summary = (f"{len(state['ranked'])} machines assessed, "
               f"{len(actions)} recommended for dispatch this week.")
    return {"actions": actions, "summary": summary}


def approval_gate(state: PlanState) -> dict:
    """HITL interrupt — the graph pauses here until the manager approves a machine."""
    decision = interrupt({
        "ranked": state.get("ranked", []),
        "actions": state.get("actions", []),
        "summary": state.get("summary", ""),
        "executed": state.get("executed", []),
    })
    return {"pending": (decision or {}).get("machine_id")}


def execute(state: PlanState) -> dict:
    """The accountable action — reached only after the manager approves at the gate."""
    mid = state.get("pending")
    row = next((r for r in state.get("ranked", []) if r["machine_id"] == mid), None)
    executed = list(state.get("executed", []))
    if row is not None:
        fault_code = row["fault_code"] or "UNSPEC"
        part_id = tools.recommended_part(row["fault_code"])
        priority = "High" if row["priority_score"] >= 12 else "Medium"
        notes = (f"[{priority}] {row['unresolved_faults']} unresolved fault(s) at "
                 f"{row['location']}. ${row['revenue_at_risk']:,}/wk at risk. "
                 f"Raised from Marc's Manager Agent dispatch plan.")
        result = tools.create_service_order(mid, fault_code, part_id, notes)
        executed.append(result)
    return {"executed": executed, "pending": None}


def _draft_message(row: dict[str, Any]) -> str:
    mgr = row["manager"]["name"]
    base = (f"Hi {mgr}, {row['machine_id']} at {row['location']} has "
            f"{row['unresolved_faults']} unresolved fault(s)"
            + (f" (code {row['fault_code']})" if row["fault_code"] else "")
            + f". Estimated ${row['revenue_at_risk']:,}/wk at risk. "
            + "I'm raising a service order — please confirm access for the technician.")
    if row.get("bulletin"):
        base += f" Reference: {row['bulletin']}"
    return base


# --- Graph -----------------------------------------------------------------
def _after_gate(state: PlanState) -> str:
    return "execute" if state.get("pending") else END


def build_graph():
    g = StateGraph(PlanState)
    for name, fn in [("assess", assess), ("quantify", quantify), ("enrich", enrich),
                     ("score", score), ("assign", assign),
                     ("approval_gate", approval_gate), ("execute", execute)]:
        g.add_node(name, fn)
    g.add_edge(START, "assess")
    g.add_edge("assess", "quantify")
    g.add_edge("quantify", "enrich")
    g.add_edge("enrich", "score")
    g.add_edge("score", "assign")
    g.add_edge("assign", "approval_gate")
    g.add_conditional_edges("approval_gate", _after_gate, {"execute": "execute", END: END})
    g.add_edge("execute", "approval_gate")
    return g.compile(checkpointer=MemorySaver())


# One compiled graph per process; MemorySaver keeps per-thread (per-session) state.
GRAPH = build_graph()


def start_plan(thread_id: str) -> dict[str, Any]:
    """Run assess→assign; pause at the approval gate; return the plan."""
    cfg = {"configurable": {"thread_id": thread_id}}
    GRAPH.invoke({"executed": []}, cfg)
    return _plan_from_state(thread_id)


def approve_machine(thread_id: str, machine_id: str) -> dict[str, Any]:
    """Resume the paused graph to execute the write-back for one approved machine."""
    cfg = {"configurable": {"thread_id": thread_id}}
    GRAPH.invoke(Command(resume={"machine_id": machine_id}), cfg)
    executed = GRAPH.get_state(cfg).values.get("executed", [])
    return executed[-1] if executed else {"status": "error", "reason": "nothing executed"}


def _plan_from_state(thread_id: str) -> dict[str, Any]:
    vals = GRAPH.get_state({"configurable": {"thread_id": thread_id}}).values
    return {"ranked": vals.get("ranked", []), "actions": vals.get("actions", []),
            "summary": vals.get("summary", ""), "executed": vals.get("executed", []),
            "thread_id": thread_id}
