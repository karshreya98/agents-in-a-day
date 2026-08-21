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

## Step 2 — Get the Lakebase instance name

A Lakebase **Database Instance** named **`sunny-bay-lakebase`** is **pre-created** for this
workshop — do **not** create a new one. Its identifier is just that name; you pass it as
`instance_name` in Step 4. (If the user gives a different name, use theirs.) Confirm it
exists with:

```bash
databricks database list-database-instances --profile <profile>
```

## Step 3 — Declare Lakebase as an app resource (`databricks.yml`)

Add the Lakebase instance as an app resource so the app's service principal can reach it,
and pass its **name** through as an env var (this is the identifier Step 4 constructs with):

```yaml
resources:
  apps:
    marc_dispatch_agent:
      name: "marc-dispatch-agent"
      source_code_path: ./
      resources:
        - name: 'database'
          database:
            instance_name: "sunny-bay-lakebase"
            database_name: "databricks_postgres"
            permission: 'CAN_CONNECT_AND_CREATE'
      config:
        env:
          - name: LAKEBASE_INSTANCE_NAME
            value: "sunny-bay-lakebase"
```

> See the bundled `lakebase-setup` skill for the exact resource YAML, including the
> **autoscaling** (`postgres` with `branch`/`database`) form if that's your instance type.
> If deploying via the Apps UI instead of the bundle, add the Lakebase instance under the
> app's **Edit → App resources → Add resource**, and set `LAKEBASE_INSTANCE_NAME` in the
> app's environment.

> [!NOTE]
> Adding the resource injects `PGHOST` / `PGUSER` / `PGDATABASE` / … into the app — but
> `AsyncCheckpointSaver` does **not** use those; it connects via the SDK using the instance
> name you pass in Step 4. The env var here is just how Step 4 receives that name.

## Step 4 — Create the Lakebase checkpointer at startup and rebind the graph

> [!IMPORTANT]
> **Two things `AsyncCheckpointSaver` requires — get these right or it silently fails:**
> 1. **Construct it with a Lakebase identifier.** It does **NOT** read `PGHOST` / `PGUSER` /
>    `PGPASSWORD` / `PGDATABASE` env vars. It connects through the Databricks SDK using the
>    instance identifier you pass. Pick the mode that matches how you created the instance:
>    - **Provisioned** (the usual "Compute → Database instances → Create" path):
>      `AsyncCheckpointSaver(instance_name="<your-instance-name>")`
>    - **Autoscaling** (project/branch/endpoint):
>      `AsyncCheckpointSaver(autoscaling_endpoint="<endpoint>", project="<p>", branch="<b>")`
> 2. **Use it as an async context manager.** The connection pool opens on `__aenter__` and
>    the checkpoint tables are created there. Do **not** build it as a bare/lazy singleton
>    and call `.setup()` on it — with no open pool that will not work. Enter it with
>    `async with ...` (a startup lifespan is the clean place) and keep it open for the app's
>    lifetime.

Its constructor signature: `AsyncCheckpointSaver(*, instance_name=None,
autoscaling_endpoint=None, project=None, branch=None, workspace_client=None, schema=None)`.

Wire it into the server lifespan in **`agent_server/start_server.py`** and rebind
`dispatch.GRAPH` to a graph that uses it. Add this after `app = agent_server.app`:

```python
import os
from contextlib import asynccontextmanager

from databricks_langchain import AsyncCheckpointSaver

from agent_server import dispatch

_original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def _lifespan(app):
    instance = os.getenv("LAKEBASE_INSTANCE_NAME")
    if not instance:
        # No Lakebase configured (e.g. local/sample mode) — keep the in-memory MemorySaver.
        async with _original_lifespan(app):
            yield
        return
    # async with opens the connection pool and creates the checkpoint tables.
    async with AsyncCheckpointSaver(instance_name=instance) as checkpointer:
        dispatch.GRAPH = dispatch.build_graph(checkpointer)  # durable short-term memory
        async with _original_lifespan(app):
            yield


app.router.lifespan_context = _lifespan
```

> Use `autoscaling_endpoint=...` / `project=...` / `branch=...` instead of `instance_name`
> if your Lakebase is an autoscaling instance. Either way, `dispatch.build_graph(checkpointer)`
> already exists and takes the checkpointer — nothing in `dispatch.py` or `agent.py` changes.

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
