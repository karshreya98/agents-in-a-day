"""Canonical MLflow **ResponsesAgent** wrapper around the LangGraph dispatch agent.

`ResponsesAgent` is the interface Databricks recommends for authoring agents — it's what
makes the agent loggable (`mlflow.pyfunc.log_model`), evaluable (`mlflow.genai.evaluate`),
and deployable (`databricks.agents.deploy`), with tracing for free. Our FastAPI cockpit
drives the graph directly for its rich UI; this class is the standard, portable surface
for everything else (a serving endpoint, the Review App, eval jobs).
"""
from __future__ import annotations

from typing import Any

from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

from .agent import get_agent


class ManagerResponsesAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        message = _last_user_text(request)
        result = get_agent().chat(message)
        text = result["reply"]
        if result.get("plan"):  # append the ranked list so the text surface is useful too
            for row in result["plan"]["ranked"]:
                text += (f"\n• {row['machine_id']} ({row['location']}) — priority "
                         f"{row['priority_score']}, {row['unresolved_faults']} unresolved")
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=text, id="msg_1")],
            custom_outputs={"intent": result.get("intent")},
        )


def _last_user_text(request: ResponsesAgentRequest) -> str:
    for item in reversed(request.input):
        data = item if isinstance(item, dict) else item.model_dump()
        if data.get("role") == "user":
            content = data.get("content", "")
            if isinstance(content, str):
                return content
            # Responses-style content: list of {type, text}
            return " ".join(p.get("text", "") for p in content if isinstance(p, dict))
    return ""


# Model instance MLflow logs/serves (`mlflow.models.set_model(AGENT)` in the driver).
AGENT = ManagerResponsesAgent()
