"""API routes for the Manager Agent app."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..agent import get_agent

router = APIRouter()


class ApproveRequest(BaseModel):
    machine_id: str
    thread_id: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.post("/chat")
def chat(req: ChatRequest) -> dict:
    """Cockpit entry point: routes the message to plan / explain / approve / qa / help."""
    history = [m.model_dump() for m in req.history]
    return get_agent().chat(req.message, history)


@router.post("/dispatch-plan")
def dispatch_plan() -> dict:
    """Run the graph to the approval interrupt; return the ranked plan + a session thread_id."""
    return get_agent().build_dispatch_plan()


@router.post("/approve")
def approve(req: ApproveRequest) -> dict:
    """Resume the paused graph past its interrupt to run the UC write-back for one machine."""
    return get_agent().approve(req.thread_id, req.machine_id)
