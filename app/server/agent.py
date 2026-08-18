"""Facade over the LangGraph dispatch graph + a lightweight intent router.

The cockpit (FastAPI) and the canonical `ResponsesAgent` both call through here. The graph
in `graph.py` is the brain; this module adds session handling, the chat router, and the
read-only helpers (explain / Genie Q&A).
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from . import config, graph, tools

try:
    import mlflow

    mlflow.langchain.autolog()  # trace every LangGraph node + LLM call
    # langgraph fires an `on_interrupt` callback that mlflow 3.15's tracer doesn't yet
    # implement — add a no-op so the HITL interrupt doesn't log a spurious error.
    from mlflow.langchain.langchain_tracer import MlflowLangchainTracer

    if not hasattr(MlflowLangchainTracer, "on_interrupt"):
        MlflowLangchainTracer.on_interrupt = lambda self, *a, **k: None
except Exception:  # pragma: no cover
    pass

_MACHINE_RE = re.compile(r"CBM[-\s]?0*(\d{1,3})", re.IGNORECASE)


class ManagerAgent:
    # --- Dispatch workflow (LangGraph, with the approval interrupt) --------
    def build_dispatch_plan(self, thread_id: str | None = None) -> dict[str, Any]:
        return graph.start_plan(thread_id or _new_thread())

    def approve(self, thread_id: str, machine_id: str) -> dict[str, Any]:
        return graph.approve_machine(thread_id, _canonical_id(machine_id) or machine_id)

    # --- Read-only helpers -------------------------------------------------
    def explain_ranking(self, machine_id: str | None) -> str:
        mid = _canonical_id(machine_id)
        plan = self.build_dispatch_plan()
        row = next((r for r in plan["ranked"] if r["machine_id"] == mid), None)
        if row is None:
            return f"I don't have {machine_id or 'that machine'} in the current plan."
        rank = plan["ranked"].index(row) + 1
        fault_pts = round(graph.FAULT_WEIGHT * row["unresolved_faults"], 1)
        rev_pts = round(graph.REVENUE_WEIGHT * row["revenue_at_risk"] / 1000, 1)
        return (f"{mid} ({row['location']}) is ranked #{rank} with score {row['priority_score']}: "
                f"{row['unresolved_faults']} unresolved fault(s) → {fault_pts} pts, plus "
                f"${row['revenue_at_risk']:,}/wk revenue at risk → {rev_pts} pts. "
                f"The formula is {graph.FAULT_WEIGHT}·faults + revenue/1000 — deterministic, so "
                f"the ranking is always reproducible.")

    def answer_question(self, question: str, genie: str | None = None) -> str:
        space = (config.SALES_GENIE_SPACE_ID if genie == "sales"
                 else config.MAINTENANCE_GENIE_SPACE_ID)
        return tools.GenieTool(space, genie or "maintenance").ask(question)

    # --- Chat cockpit: route one message -----------------------------------
    def chat(self, message: str, history: list[dict] | None = None) -> dict[str, Any]:
        intent = self._route(message, history or [])
        kind = intent.get("intent", "help")

        if kind == "dispatch_plan":
            plan = self.build_dispatch_plan()
            return {"intent": kind, "plan": plan,
                    "reply": plan["summary"] + " Ranked below — approve any card to raise "
                    "its service order."}

        if kind == "explain":
            return {"intent": kind, "reply": self.explain_ranking(intent.get("machine_id"))}

        if kind == "approve":
            mid = _canonical_id(intent.get("machine_id"))
            if not mid:
                return {"intent": kind, "reply": "Which machine should I raise the order for? "
                        "Name it, e.g. 'approve CBM-003'."}
            plan = self.build_dispatch_plan()          # fresh session
            res = self.approve(plan["thread_id"], mid)
            if res.get("status") == "created":
                return {"intent": kind, "reply": f"✅ Raised service order {res['order_id']} for "
                        f"{mid} (part {res.get('part_id')})."}
            return {"intent": kind, "reply": f"Couldn't raise the order for {mid}: "
                    f"{res.get('reason', res.get('status'))}."}

        if kind == "qa":
            return {"intent": kind, "reply": self.answer_question(
                intent.get("question") or message, intent.get("genie"))}

        return {"intent": "help", "reply": (
            "I'm Marc's operations agent. Try: 'build my dispatch plan', "
            "'why is CBM-003 ranked first?', 'what's the revenue at North Beach?', "
            "or 'approve CBM-003'.")}

    def _route(self, message: str, history: list[dict]) -> dict[str, Any]:
        if not config.DRY_RUN:
            try:
                return tools.llm_route(message, history)
            except Exception:
                pass  # fall back to rules if the LLM is unavailable
        return _route_rules(message)


def _new_thread() -> str:
    return uuid.uuid4().hex


def _canonical_id(raw: str | None) -> str | None:
    if not raw:
        return None
    m = _MACHINE_RE.search(raw)
    return f"CBM-{int(m.group(1)):03d}" if m else None


def _route_rules(message: str) -> dict[str, Any]:
    """Deterministic keyword router — used in dry-run and as the live fallback."""
    m = message.lower()
    mid = _canonical_id(message)
    if any(k in m for k in ["dispatch", "plan", "prioriti", "this week", "what should i do"]):
        return {"intent": "dispatch_plan"}
    if mid and any(k in m for k in ["approve", "go ahead", "raise", "create the order",
                                    "create service order", "create a service order"]):
        return {"intent": "approve", "machine_id": mid}
    if mid and any(k in m for k in ["why", "explain", "ranked", "rank", "top", "first"]):
        return {"intent": "explain", "machine_id": mid}
    if mid or any(k in m for k in ["revenue", "sales", "profit", "store", "fault", "faults",
                                   "machine", "report", "which machines", "unresolved"]):
        genie = "sales" if any(k in m for k in ["revenue", "sales", "profit", "store"]) else "maintenance"
        return {"intent": "qa", "genie": genie, "question": message}
    return {"intent": "help"}


def get_agent() -> ManagerAgent:
    return ManagerAgent()
