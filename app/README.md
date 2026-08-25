# Marc's Dispatch Agent — Databricks App (Lab 3)

This app is built **on the official
[`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph)
template**, unchanged in structure: the same `agent_server/` layout, `ResponsesAgent`
handlers, `scripts/quickstart`, `app.yaml`, and built-in chat UI (served via the agent
server's chat proxy — no separate frontend).

What we changed is the **agent itself**. Instead of the template's generic tool-calling
loop, `agent_server/agent.py` drives an **explicit LangGraph pipeline with a
human-in-the-loop approval gate** — the point of Lab 3.

```
assess → score → approval_gate ⇄ execute
 Genies   Python   (interrupt)    create_service_order (UC fn)
```

- `agent_server/dispatch.py` — the LangGraph `StateGraph`: nodes, edges, the approval
  `interrupt`, the deterministic scoring policy (`FAULT_WEIGHT` / `REVENUE_WEIGHT` — the
  **Lab 3 · Task 2** edit point), and the chat-formatting helpers.
- `agent_server/tools.py` — the tool palette: two Genie spaces, the `create_service_order`
  UC function, the `location_managers` roster.
- `agent_server/agent.py` — the template's `@invoke()` / `@stream()` handlers, routing each
  message (plan / explain / qa / approve) and keying the graph thread by conversation id so
  the approval gate persists across turns.
- `agent_server/start_server.py`, `utils.py`, `scripts/` — unchanged from the template.

Because it's a plain chat UI, the approval gate is a **conversation**: "build my dispatch
plan" pauses at the gate and returns the ranked plan; replying **"approve CBM-003"** in the
same chat resumes the graph and runs the gated write-back.

## Run it locally (dry-run, no workspace)

```bash
cd app
uv sync
AGENT_DRY_RUN=1 uv run start-server     # agent API + chat UI, canned Sunny Bay data
```

`AGENT_DRY_RUN=1` makes every tool return canned data, so you can see the full flow —
ranking, drafted messages, and the approval gate — with no Databricks calls.

## Deploy (sample-data mode)

`app.yaml` sets `AGENT_DRY_RUN=1`, so the app deploys and runs on built-in Sunny Bay data
with **no resources or config to wire up** — create the app in the Apps UI (or
`uv run quickstart` + the template `deploy` skill) and deploy. Traces still log to the
MLflow experiment in `MLFLOW_EXPERIMENT_NAME`.

## Go live

Drop `AGENT_DRY_RUN`, set the two Genie space IDs + `CATALOG`, and add a **SQL warehouse**
(for the `create_service_order` write-back) and your **Genie spaces** as app resources —
that's the live-data follow-on after **Lab 3**. Governed model and MCP blocks are **Lab 4**.

## Test

```bash
AGENT_DRY_RUN=1 uv run pytest tests/ -q
```
