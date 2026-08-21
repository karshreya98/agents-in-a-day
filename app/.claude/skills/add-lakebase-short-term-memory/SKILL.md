---
name: add-lakebase-short-term-memory
description: "Add durable SHORT-TERM agent memory to this dispatch-agent app, backed by Lakebase. Use when the user says 'add memory', 'short-term memory', 'lakebase memory', 'make the approval survive a restart', or 'persist conversation state'. This is the Lab 3 · Task 3 change: replace the in-memory MemorySaver checkpointer with a Lakebase AsyncCheckpointSaver."
---

# Add Lakebase-backed short-term memory to this app

**Goal:** the agent's short-term memory (the in-progress dispatch plan + the pending
approval, keyed by conversation `thread_id`) currently lives in an in-memory
`MemorySaver()` and is lost on restart. Move it to **Lakebase** (managed Postgres) via
LangGraph's `AsyncCheckpointSaver` so it is durable.

> This app is the basic `agent-langgraph` template. It already runs the graph **async** and
> already isolates the checkpointer in `build_checkpointer()` / `build_graph(checkpointer)`
> in `agent_server/dispatch.py`. You only need to (a) add a dependency, (b) wire Lakebase as
> a resource, and (c) create the Lakebase checkpointer at startup and rebind the graph.
> **Do not** change the graph nodes (`assess`, `score`, `approval_gate`, `execute`) or the
> approval `interrupt`. Short-term only — do **not** add the long-term `AsyncDatabricksStore`.

> **Profile reminder:** every `databricks` CLI command needs the profile from `.env`:
> `databricks <cmd> --profile <profile>`.

## Step 1 — Add the memory dependency

In `pyproject.toml`, change the `databricks-langchain` dependency to include the `memory`
extra:

```toml
dependencies = [
    "databricks-langchain[memory]>=0.17.0",
    # ...leave the other dependencies unchanged...
]
```

## Step 2 — Get a Lakebase instance

The user creates one in the UI: **Compute → Database instances → Create database instance**.
You need its **autoscaling endpoint** (a short endpoint name or the full
`projects/<project>/branches/<branch>/endpoints/<endpoint>` path), or the **project +
branch**. See the bundled `lakebase-setup` skill for the API calls to list these:

```bash
databricks api get /api/2.0/postgres/projects --profile <profile>
```

## Step 3 — Declare Lakebase as an app resource (`databricks.yml`)

Add a `postgres` resource under the app, and pass the endpoint through as an env var:

```yaml
resources:
  apps:
    marc_dispatch_agent:
      name: "marc-dispatch-agent"
      source_code_path: ./
      resources:
        - name: 'postgres'
          postgres:
            branch: "projects/<project>/branches/<branch>"
            database: "projects/<project>/branches/<branch>/databases/<database-id>"
            permission: 'CAN_CONNECT_AND_CREATE'
      config:
        env:
          - name: LAKEBASE_AUTOSCALING_ENDPOINT
            value: "<your-endpoint-or-projects/p/branches/b/endpoints/e>"
```

> If deploying via the Apps UI instead of the bundle, add the Lakebase instance under the
> app's **Edit → App resources → Add resource**, and set `LAKEBASE_AUTOSCALING_ENDPOINT` in
> the app's environment.

## Step 4 — Create the Lakebase checkpointer at startup and rebind the graph

`AsyncCheckpointSaver` is an async context manager that needs `await checkpointer.setup()`
once (to create the checkpoint tables) and should stay open for the app's lifetime. Wire it
into the server's lifespan in **`agent_server/start_server.py`**, and rebind
`dispatch.GRAPH` to a graph that uses it. Add this after `app = agent_server.app`:

```python
import os
from contextlib import asynccontextmanager

from databricks_langchain import AsyncCheckpointSaver

from agent_server import dispatch

_original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def _lifespan(app):
    endpoint = os.getenv("LAKEBASE_AUTOSCALING_ENDPOINT")
    if not endpoint:
        # No Lakebase configured (e.g. local/sample mode) — keep in-memory MemorySaver.
        async with _original_lifespan(app):
            yield
        return
    async with AsyncCheckpointSaver(autoscaling_endpoint=endpoint) as checkpointer:
        await checkpointer.setup()                       # create checkpoint tables (once)
        dispatch.GRAPH = dispatch.build_graph(checkpointer)  # durable short-term memory
        async with _original_lifespan(app):
            yield


app.router.lifespan_context = _lifespan
```

That's the whole code change — `dispatch.build_graph(checkpointer)` already exists and takes
the checkpointer; nothing else in `dispatch.py` or `agent.py` needs to change.

## Step 5 — Grant the app's service principal access to Lakebase

After deploy, the app's service principal must be able to connect and create tables. Find
the SP with `databricks apps get marc-dispatch-agent --profile <profile>`, then grant it on
the Lakebase database (see the `lakebase-setup` skill for the exact `GRANT` SQL).

## Step 6 — Verify durability

1. Redeploy the app and wait for **Running**.
2. In the chat: **"Build my dispatch plan"**.
3. **Restart the app** from its page.
4. **"approve CBM-003"** → it still works, because the plan + pending approval were read back
   from Lakebase, not memory. (Before this change, the approval would fail after a restart.)
