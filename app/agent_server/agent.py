"""Marc's dispatch agent, authored on the agent-langgraph template's server surface.

The template ships a generic tool-calling `create_agent` loop. We keep the template's
`ResponsesAgent` handlers and session handling, but drive an **explicit LangGraph pipeline
with a human-in-the-loop approval gate** (see `dispatch.py`) — the whole point of Lab 3. Each
message is traced as one MLflow span tree (a root AGENT span here, node/tool spans in
`dispatch.py`). The graph's thread is keyed by the signed-in user (see `_thread_id`), so a
plan pauses at the gate and a later "approve CBM-003" resumes it — and, because that key is
stable across restarts, the Lakebase checkpointer swap makes the plan survive one.
"""
import logging
from typing import AsyncGenerator

import mlflow
from langchain_core.messages import AIMessage
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    output_to_responses_items_stream,
)

from agent_server import dispatch
from agent_server.utils import get_session_id

logger = logging.getLogger(__name__)

# We trace the agent EXPLICITLY: a root span per message (see `build_reply` below) plus one
# span per LangGraph node and tool call (see dispatch.py). We deliberately do NOT use
# `mlflow.langchain.autolog()` here — its callback-based spans would duplicate our explicit
# node spans, and our sync graph nodes run in a worker thread that autolog's tracing context
# doesn't stitch together cleanly. Explicit tracing yields one clean AGENT → nodes → tools tree.

HELP = (
    "I'm Marc's dispatch agent. Try:\n"
    "- **\"Build my dispatch plan\"** — rank this week's machines by priority\n"
    "- **\"Why is CBM-003 ranked first?\"** — explain a machine's score\n"
    "- **\"What's the weekly revenue by store?\"** — ask the Sales Genie\n"
    "- **\"Approve CBM-003\"** — raise the gated service order for a machine"
)


def _latest_user_text(request: ResponsesAgentRequest) -> str:
    for item in reversed(request.input or []):
        d = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        if d.get("role") != "user":
            continue
        content = d.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = [c.get("text", "") for c in content if isinstance(c, dict)]
            return " ".join(p for p in parts if p).strip()
    return ""


def _is_title_request(request: ResponsesAgentRequest) -> bool:
    """The chat UI names each conversation by asking the agent for a 'short title'. Detect
    that system prompt so we return a title instead of running the dispatch pipeline (which
    would dump the full response into the header)."""
    for item in (request.input or []):
        d = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        if d.get("role") != "system":
            continue
        content = d.get("content")
        text = content if isinstance(content, str) else (
            " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            if isinstance(content, list) else "")
        if "short title" in (text or "").lower():
            return True
    return False


def _title_from(request: ResponsesAgentRequest) -> str:
    """A short, plain-text conversation title from the user's first message."""
    import json

    text = _latest_user_text(request)
    try:  # the UI sends the message as a JSON blob — pull the inner text out
        obj = json.loads(text)
        inner = " ".join(p.get("text", "") for p in obj.get("parts", [])
                         if isinstance(p, dict) and p.get("type") == "text").strip()
        text = inner or text
    except Exception:
        pass
    return (text or "Marc's dispatch agent")[:70]


def _route(text: str) -> str:
    """Deterministic intent router (offline-friendly). `dispatch.llm_route` is available
    for a Foundation-Model router when running live."""
    t = text.lower()
    if "approve" in t or ("create" in t and "order" in t):
        return "approve"
    if t.startswith("why") or "explain" in t:
        return "explain"
    if "dispatch" in t or "plan" in t or "prioriti" in t:
        return "dispatch_plan"
    if any(k in t for k in ("revenue", "sales", "profit", "store")):
        return "qa_sales"
    if any(k in t for k in ("fault", "unresolved", "machine", "broken")):
        return "qa_maintenance"
    return "help"


def _thread_id(request: ResponsesAgentRequest) -> str:
    """Stable memory key across app restarts, so durable memory is demonstrable. Prefer the
    signed-in user (per-user working memory); fall back to a fixed key. We deliberately do
    NOT key on the chat UI's conversation id — it changes when the app restarts, which would
    make the restored plan look 'lost'."""
    uid = None
    if request.context and getattr(request.context, "user_id", None):
        uid = request.context.user_id
    if not uid and isinstance(request.custom_inputs, dict):
        uid = request.custom_inputs.get("user_id")
    return f"user:{uid}" if uid else "default"


@mlflow.trace(span_type="AGENT", name="dispatch_agent")
async def build_reply(request: ResponsesAgentRequest) -> str:
    if _is_title_request(request):        # the chat UI naming the conversation
        return _title_from(request)
    thread_id = _thread_id(request)
    text = _latest_user_text(request)
    intent = _route(text)

    if intent == "approve":
        # Resume the plan paused at the approval gate. We do NOT silently rebuild it — an
        # approve only works if there's a plan in progress for this conversation. That's
        # what makes memory observable: after a restart, the plan is restored from the
        # checkpointer (Lakebase → survives; in-memory → gone, so this asks you to rebuild).
        if not await dispatch._has_plan(thread_id):
            return ("I don't have a dispatch plan in progress for this conversation — say "
                    "**\"build my dispatch plan\"** first, then approve a machine.")
        order = await dispatch.approve_machine(thread_id, text)
        return dispatch.format_order(order)
    if intent == "explain":
        return await dispatch.explain_ranking(thread_id, text)
    if intent == "qa_sales":
        return dispatch.answer_question(text, genie="sales")
    if intent == "qa_maintenance":
        return dispatch.answer_question(text, genie="maintenance")
    if intent == "dispatch_plan":
        return dispatch.format_plan(await dispatch.build_plan(thread_id))
    return HELP


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})
    reply = await build_reply(request)
    for item in output_to_responses_items_stream([AIMessage(content=reply)]):
        yield item
