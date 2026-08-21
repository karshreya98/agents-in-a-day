---
name: add-lakebase-short-term-memory
description: "Add durable SHORT-TERM agent memory to this dispatch-agent app, backed by Lakebase. Use when the user says 'add memory', 'short-term memory', 'lakebase memory', 'make the approval survive a restart', or 'persist conversation state'. This is Lab 3 · Task 3: move the checkpointer from in-memory MemorySaver to a Lakebase AsyncCheckpointSaver."
---

# Add Lakebase-backed short-term memory (Lab 3 · Task 3)

**Goal:** move the agent's short-term memory — the in-progress dispatch plan and the pending
approval, keyed by conversation `thread_id` — from the in-memory `MemorySaver()` to
**Lakebase** so it survives an app restart.

> **Almost everything is already wired in this repo. Make ONE change.**
> - `pyproject.toml` already has `databricks-langchain[memory]`.
> - `databricks.yml` already declares the Lakebase instance `sunny-bay-lakebase` as an app
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
    async with AsyncCheckpointSaver(instance_name="sunny-bay-lakebase") as checkpointer:
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

## Verify

1. Redeploy the app; wait for **Running**.
2. Chat: **"Build my dispatch plan"** → **restart the app** → **"approve CBM-003"**. It still
   works, because the plan and pending approval were read back from Lakebase, not memory.
