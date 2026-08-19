"""Marc's dispatch agent as an explicit **LangGraph** StateGraph.

This is the "control flow you own": not a generic tool-calling loop, but a graph you can
read node-by-node, with a **human-in-the-loop `interrupt`** as the approval gate before the
`create_service_order` write-back.

    assess → score → approval_gate ⇄ execute
                        (interrupt)   (write-back)

`mlflow.langchain.autolog()` (enabled in agent.py) traces every node automatically. A
MemorySaver checkpointer lets the graph pause at the interrupt and resume when the manager
approves — the canonical LangGraph HITL pattern. The chat surface (agent.py) keys each
LangGraph thread by the conversation id, so "build my plan" pauses at the gate and a later
"approve CBM-003" in the same conversation resumes it.
"""
from __future__ import annotations

import re
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

_MACHINE_RE = re.compile(r"CBM[-\s]?0*(\d{1,3})", re.IGNORECASE)


class PlanState(TypedDict, total=False):
    fleet: list[dict[str, Any]]
    ranked: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    executed: list[dict[str, Any]]
    summary: str
    pending: Optional[str]


# --- Nodes -----------------------------------------------------------------
def assess(state: PlanState) -> dict:
    """Ask the Genies which machines have unresolved faults and each store's revenue."""
    maintenance = tools.GenieTool(tools.config.MAINTENANCE_GENIE_SPACE_ID, "Maintenance Genie")
    faults = maintenance.ask(
        "Which machines across all locations have unresolved faults, with their fault codes?")
    sales = tools.GenieTool(tools.config.SALES_GENIE_SPACE_ID, "Sales Genie")
    sales.ask("What is the weekly coffee revenue by store?")
    fleet = tools.parse_fleet(faults)
    for row in fleet:
        row["revenue_at_risk"] = row["weekly_revenue"]  # a down machine risks its store's revenue
    return {"fleet": fleet}


def score(state: PlanState) -> dict:
    """Rank machines by priority and draft a message for the ones worth dispatching."""
    ranked = sorted(state["fleet"], key=_priority, reverse=True)
    for row in ranked:
        row["priority_score"] = _priority(row)
    actions = []
    for row in ranked:
        if row["unresolved_faults"] and row["priority_score"] >= DISPATCH_THRESHOLD:
            row["draft_message"] = _draft_message(row)
            row["needs_approval"] = True
            actions.append(row)
    summary = (f"{len(ranked)} machines assessed, "
               f"{len(actions)} recommended for dispatch this week.")
    return {"ranked": ranked, "actions": actions, "summary": summary}


def _priority(row: dict[str, Any]) -> float:
    return round(FAULT_WEIGHT * row["unresolved_faults"]
                 + REVENUE_WEIGHT * row["revenue_at_risk"] / 1000, 2)


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
                 f"Raised from Marc's dispatch agent.")
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
    for name, fn in [("assess", assess), ("score", score),
                     ("approval_gate", approval_gate), ("execute", execute)]:
        g.add_node(name, fn)
    g.add_edge(START, "assess")
    g.add_edge("assess", "score")   # LAB 3 · TASK 2: try inserting a node here (assess → your_node → score)
    g.add_edge("score", "approval_gate")
    g.add_conditional_edges("approval_gate", _after_gate, {"execute": "execute", END: END})
    g.add_edge("execute", "approval_gate")
    return g.compile(checkpointer=MemorySaver())


# One compiled graph per process; MemorySaver keeps per-thread (per-conversation) state.
GRAPH = build_graph()


# --- Orchestration the chat surface calls ----------------------------------
def build_plan(thread_id: str) -> dict[str, Any]:
    """Run assess→assign; pause at the approval gate; return the plan."""
    cfg = {"configurable": {"thread_id": thread_id}}
    GRAPH.invoke({"executed": []}, cfg)
    return _plan_from_state(thread_id)


def approve_machine(thread_id: str, machine_id: str) -> dict[str, Any]:
    """Resume the paused graph to execute the write-back for one approved machine."""
    cfg = {"configurable": {"thread_id": thread_id}}
    GRAPH.invoke(Command(resume={"machine_id": canonical_id(machine_id) or machine_id}), cfg)
    executed = GRAPH.get_state(cfg).values.get("executed", [])
    return executed[-1] if executed else {"status": "error", "reason": "nothing executed"}


def _plan_from_state(thread_id: str) -> dict[str, Any]:
    vals = GRAPH.get_state({"configurable": {"thread_id": thread_id}}).values
    return {"ranked": vals.get("ranked", []), "actions": vals.get("actions", []),
            "summary": vals.get("summary", ""), "executed": vals.get("executed", [])}


def explain_ranking(thread_id: str, machine_id: str | None) -> str:
    mid = canonical_id(machine_id)
    plan = build_plan(thread_id) if not _has_plan(thread_id) else _plan_from_state(thread_id)
    row = next((r for r in plan["ranked"] if r["machine_id"] == mid), None)
    if row is None:
        return f"I don't have {machine_id or 'that machine'} in the current plan."
    rank = plan["ranked"].index(row) + 1
    fault_pts = round(FAULT_WEIGHT * row["unresolved_faults"], 1)
    rev_pts = round(REVENUE_WEIGHT * row["revenue_at_risk"] / 1000, 1)
    return (f"**{mid} ({row['location']})** is ranked #{rank} with score "
            f"**{row['priority_score']}**: {row['unresolved_faults']} unresolved fault(s) → "
            f"{fault_pts} pts, plus ${row['revenue_at_risk']:,}/wk revenue at risk → {rev_pts} "
            f"pts. Formula: {FAULT_WEIGHT}·faults + revenue/1000 — deterministic, so the "
            f"ranking is always reproducible.")


def answer_question(question: str, genie: str | None = None) -> str:
    cfg = tools.config
    space = cfg.SALES_GENIE_SPACE_ID if genie == "sales" else cfg.MAINTENANCE_GENIE_SPACE_ID
    return tools.GenieTool(space, genie or "maintenance").ask(question)


def _has_plan(thread_id: str) -> bool:
    return bool(GRAPH.get_state({"configurable": {"thread_id": thread_id}}).values.get("ranked"))


def canonical_id(text: str | None) -> str | None:
    if not text:
        return None
    m = _MACHINE_RE.search(text)
    return f"CBM-{int(m.group(1)):03d}" if m else None


# --- Formatting the plan for the chat UI -----------------------------------
def format_plan(plan: dict[str, Any]) -> str:
    ranked = plan.get("ranked", [])
    if not ranked:
        return "No machines to assess right now."
    lines = [f"**Dispatch plan** — {plan.get('summary', '')}", ""]
    for i, row in enumerate(ranked, 1):
        flag = " ⚠️ **needs approval**" if row.get("needs_approval") else ""
        lines.append(
            f"**{i}. {row['machine_id']} — {row['location']}** · score "
            f"{row['priority_score']}{flag}\n"
            f"   - {row['unresolved_faults']} unresolved fault(s)"
            + (f", code {row['fault_code']}" if row.get("fault_code") else "")
            + f" · ${row.get('revenue_at_risk', 0):,}/wk at risk")
        if row.get("draft_message"):
            lines.append(f"   - _Draft to {row['manager']['name']}:_ {row['draft_message']}")
    staged = [r["machine_id"] for r in plan.get("actions", [])]
    if staged:
        lines += ["", f"Reply **\"approve {staged[0]}\"** to raise the service order — "
                      "nothing is written until you approve."]
    return "\n".join(lines)


def format_order(order: dict[str, Any]) -> str:
    if order.get("status") != "created":
        return f"I couldn't raise that order: {order.get('reason', 'unknown error')}."
    return (f"✅ Service order **{order.get('order_id')}** created for "
            f"**{order.get('machine_id')}** (part {order.get('part_id')}). "
            "The write-back ran only after your approval.")
