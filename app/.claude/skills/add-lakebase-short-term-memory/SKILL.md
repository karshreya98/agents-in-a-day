---
name: add-lakebase-short-term-memory
description: "Add durable SHORT-TERM agent memory to this dispatch-agent app, backed by Lakebase. Use when the user says 'add memory', 'short-term memory', 'lakebase memory', 'make the approval survive a restart', or 'persist conversation state'. This is Lab 3 · Task 3: move the checkpointer from in-memory MemorySaver to a Lakebase AsyncCheckpointSaver."
---

# Add Lakebase-backed short-term memory (Lab 3 · Task 3)

**Goal:** move the agent's short-term memory — the in-progress dispatch plan and the pending
approval — from the in-memory `MemorySaver()` to **Lakebase** so it survives an app restart.

> **Almost everything is already wired in this repo. Make ONE change.**
> - `pyproject.toml` already has `databricks-langchain[memory]`.
> - `databricks.yml` already declares the Lakebase instance `sunny-bay-roastery-lakebase` as an app
>   resource.
> - `agent_server/dispatch.py` already exposes `build_graph(checkpointer)` and runs the
>   graph async.
>
> **Do NOT** re-add the dependency or the resource, **do NOT** edit `dispatch.py`, `app.yaml`,
> `pyproject.toml`, or `databricks.yml`, and **do NOT** change the graph nodes or the approval
> gate. Only edit `agent_server/start_server.py`.

## The one change — `agent_server/start_server.py`

Add this right after `app = agent_server.app`:

```python
import os
from contextlib import asynccontextmanager

from databricks_langchain import AsyncCheckpointSaver

from agent_server import dispatch

_original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def _lifespan(app):
    # Local/dev (not deployed as a Databricks App): keep the in-memory MemorySaver.
    if not os.getenv("DATABRICKS_APP_NAME"):
        async with _original_lifespan(app):
            yield
        return
    # Deployed: durable short-term memory on the pre-created Lakebase instance.
    async with AsyncCheckpointSaver(
        instance_name="sunny-bay-roastery-lakebase",
        schema="agent_memory",   # REQUIRED — see note below; the app SP can't write to `public`
    ) as checkpointer:
        await checkpointer.setup()                           # REQUIRED — creates the tables
        dispatch.GRAPH = dispatch.build_graph(checkpointer)  # rebind graph to Lakebase memory
        async with _original_lifespan(app):
            yield


app.router.lifespan_context = _lifespan
```

Two things that MUST be right, or it silently fails:

1. **`await checkpointer.setup()`** creates the `checkpoints` / `checkpoint_writes` tables.
   Skip it and the first request errors with `relation "checkpoints" does not exist`.
2. **Enter it with `async with`** (that opens the connection pool). Never build a bare/lazy
   singleton — it has no open pool.
3. **`schema="agent_memory"`** is not optional. The deployed app connects as its **service
   principal**, which can *connect* to the database but does **not** own the default `public`
   schema — so `setup()`'s `CREATE TABLE` there fails with
   `psycopg.errors.InsufficientPrivilege: permission denied for schema public` and the app
   **crashes on startup**. Passing a `schema` makes `setup()` run `CREATE SCHEMA IF NOT EXISTS
   agent_memory` first — which the SP *is* allowed to do (that's what `CAN_CONNECT_AND_CREATE`
   grants) — and it owns that schema, so the tables create cleanly. (Running locally as
   yourself works without it because you own `public`; that hides the bug until deploy.)

## Attach the Lakebase instance to the app — BEFORE redeploying

After you make the code edit, tell the user to attach the instance as an app resource, and be
explicit that this happens **before** the redeploy. The app opens a Lakebase connection at
startup, so the resource must already be attached or the app **crashes on startup**.

> Tell the user, in the app UI: **Edit → App resources → Add resource → Database instance →
> `sunny-bay-roastery-lakebase` → permission `CAN_CONNECT_AND_CREATE` → Save.**
>
> - This is a UI step, not a code change — **don't** try to do it from code.
> - The permission **must be `CAN_CONNECT_AND_CREATE`, not `CAN_CONNECT`** — the app creates
>   its own `agent_memory` schema on first start, which needs the CREATE grant. With only
>   `CAN_CONNECT` it crashes with `permission denied for schema public`.

## Redeploy and verify

> **Redeploy from the Databricks UI — do NOT run any CLI / `databricks apps deploy` /
> bundle commands.** Just tell the user: *on the app's page in the workspace, click
> **Deploy** to re-sync the edited code, then wait for **Running**.*

1. Confirm the resource is attached (above), then redeploy via the UI; wait for **Running**.
   If it shows **Crashed**, the attach/permission from the previous section is the usual cause.
2. Chat: **"Build my dispatch plan"** → **restart the app** → **"approve CBM-003"**. It still
   works, because the plan and pending approval were read back from Lakebase, not memory.
