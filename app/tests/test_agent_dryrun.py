"""Offline smoke tests for the LangGraph dispatch agent — no workspace (AGENT_DRY_RUN=1).

Covers the control flow, the approval interrupt/resume, the chat router, and the canonical
ResponsesAgent wrapper.
"""
import os

os.environ["AGENT_DRY_RUN"] = "1"

from server.agent import get_agent  # noqa: E402


def test_dispatch_plan_ranks_and_stages_without_writing():
    plan = get_agent().build_dispatch_plan()
    scores = [r["priority_score"] for r in plan["ranked"]]
    assert scores == sorted(scores, reverse=True)
    ids = [r["machine_id"] for r in plan["ranked"]]
    assert ids.index("CBM-003") < ids.index("CBM-011")
    assert plan["actions"] and all(a["needs_approval"] for a in plan["actions"])
    assert plan["executed"] == [], "the interrupt must pause BEFORE any write-back"
    assert plan["thread_id"]


def test_actions_have_drafts_to_the_right_manager():
    for a in get_agent().build_dispatch_plan()["actions"]:
        assert a["manager"]["name"] in a["draft_message"]


def test_approval_interrupt_resume_writes_back():
    agent = get_agent()
    plan = agent.build_dispatch_plan()
    res = agent.approve(plan["thread_id"], "CBM-003")
    assert res["status"] == "created" and res["machine_id"] == "CBM-003"
    assert res["part_id"] == "SIE-EQ9-PUMP-003"


def test_chat_routes_to_dispatch_plan():
    r = get_agent().chat("build my dispatch plan for this week")
    assert r["intent"] == "dispatch_plan" and r["plan"]["thread_id"]


def test_chat_explains_ranking_with_math():
    r = get_agent().chat("why is CBM-003 ranked first?")
    assert r["intent"] == "explain" and "#1" in r["reply"] and "pts" in r["reply"]


def test_chat_qa_routes_to_sales():
    r = get_agent().chat("what's the weekly revenue by store?")
    assert r["intent"] == "qa" and "revenue" in r["reply"].lower()


def test_chat_approve_executes_write_back():
    r = get_agent().chat("approve CBM-003 and raise the order")
    assert r["intent"] == "approve" and "SO-DRYRUN-CBM-003" in r["reply"]


def test_chat_help_fallback():
    assert get_agent().chat("hello there")["intent"] == "help"


def test_responses_agent_returns_text_output():
    from mlflow.types.responses import ResponsesAgentRequest

    from server.responses_agent import ManagerResponsesAgent

    resp = ManagerResponsesAgent().predict(
        ResponsesAgentRequest(input=[{"role": "user", "content": "build my dispatch plan"}]))
    assert resp.output and "recommended for dispatch" in str(resp.model_dump())
