"""Dry-run tests for Marc's dispatch pipeline — no workspace calls."""
import os

os.environ.setdefault("AGENT_DRY_RUN", "1")

from agent_server import dispatch  # noqa: E402


def test_plan_ranks_mission_first():
    plan = dispatch.build_plan("t-rank")
    assert plan["ranked"][0]["machine_id"] == "CBM-003"  # 3 faults + high revenue
    assert plan["summary"]


def test_gate_holds_until_approved():
    plan = dispatch.build_plan("t-gate")
    assert plan["executed"] == []  # the approval gate wrote nothing


def test_approve_creates_order():
    dispatch.build_plan("t-appr")
    order = dispatch.approve_machine("t-appr", "CBM-003")
    assert order["status"] == "created"
    assert order["machine_id"] == "CBM-003"


def test_scoring_is_deterministic_and_weighted():
    plan = dispatch.build_plan("t-score")
    top = plan["ranked"][0]
    expected = round(dispatch.FAULT_WEIGHT * top["unresolved_faults"]
                     + dispatch.REVENUE_WEIGHT * top["revenue_at_risk"] / 1000, 2)
    assert top["priority_score"] == expected


def test_canonical_id():
    assert dispatch.canonical_id("approve cbm 3") == "CBM-003"
    assert dispatch.canonical_id("why is CBM-009 ranked?") == "CBM-009"
    assert dispatch.canonical_id("no machine here") is None


def test_explain_mentions_score():
    txt = dispatch.explain_ranking("t-exp", "CBM-003")
    assert "CBM-003" in txt and "score" in txt.lower()


def test_router_maps_the_four_lab_prompts():
    from agent_server.agent import _route

    assert _route("Build my dispatch plan") == "dispatch_plan"
    assert _route("Approve CBM-003") == "approve"
    assert _route("Why is CBM-003 ranked first?") == "explain"
    assert _route("What's the weekly revenue by store?") == "qa_sales"
