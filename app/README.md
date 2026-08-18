# Marc's Manager Agent — Databricks App (Lab 3)

A **custom agent** deployed as a Databricks App: a React chat cockpit + FastAPI backend
with a **LangGraph** agent (wrapped in an MLflow `ResponsesAgent`) running inside it. This
is the Lab 3 deliverable and the replacement for the deprecated Agent Bricks Supervisor.
It follows the official
[`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph)
pattern (LangGraph + `ResponsesAgent` + `mlflow.langchain.autolog`), with our own cockpit UI.

## What it does

The dispatch plan is an explicit LangGraph graph with a human-in-the-loop interrupt:

```
assess → quantify → enrich → score → assign → approval_gate ⇄ execute
 Genie     Genie      MCP     Python  roster    (interrupt)    create_service_order (UC fn)
```

The UI is a **chat cockpit**: `chat()` in `server/agent.py` routes each message (LLM when
live, keyword router in dry-run) to *plan / explain / qa / approve / help*.

- `server/graph.py` — the LangGraph `StateGraph`: nodes, edges, and the approval `interrupt`.
- `server/responses_agent.py` — the graph wrapped in an MLflow `ResponsesAgent` (loggable /
  evaluable / deployable).
- `server/agent.py` — the chat router + session handling + read-only helpers.
- `server/tools.py` — the tool palette: 2 Genie spaces, you.com MCP, the
  `create_service_order` UC function, the `location_managers` roster, the LLM router.
- `server/routes/chat.py` — `POST /api/chat`, `POST /api/dispatch-plan`, `POST /api/approve`.

`/api/dispatch-plan` runs the graph to the interrupt and returns a `thread_id`;
`/api/approve` resumes that thread to run the write-back for one machine.

## Run it offline (no workspace)

```bash
cd app
uv sync
AGENT_DRY_RUN=1 uv run uvicorn app:app --port 8000     # canned Sunny Bay data
# frontend dev server (optional): cd frontend && npm install && npm run dev
```

Then open http://localhost:8000. `AGENT_DRY_RUN=1` returns canned data so you can see the
full flow — ranking, drafted messages, and the approval gate — with no Databricks calls.

## Test

```bash
AGENT_DRY_RUN=1 uv run pytest tests/ -q
```

## Deploy (live)

Set the Genie space IDs and catalog in `app.yaml`, then:

```bash
cd frontend && npm install && npm run build && cd ..
databricks apps create marc-manager-agent
databricks sync . /Workspace/Users/<you>/marc-manager-agent \
  --exclude node_modules --exclude .venv --exclude frontend/src
databricks apps deploy marc-manager-agent \
  --source-code-path /Workspace/Users/<you>/marc-manager-agent
```

Add a **Model serving endpoint** and **SQL warehouse** as app resources, then redeploy.
MLflow traces log to the experiment named in `MLFLOW_EXPERIMENT` (default
`/Shared/marc-manager-agent`); the Review App runs as a labeling session over them.
