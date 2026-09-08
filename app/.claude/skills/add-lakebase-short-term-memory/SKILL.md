---
name: add-lakebase-short-term-memory
description: "Add durable SHORT-TERM agent memory to this dispatch-agent app, backed by Lakebase. Use when the user says 'add memory', 'short-term memory', 'lakebase memory', 'make the approval survive a restart', or 'persist conversation state'. This is Lab 3 · Task 3: move the checkpointer from in-memory MemorySaver to a Lakebase AsyncCheckpointSaver, using the participant's OWN Lakebase project."
---

# Add Lakebase-backed short-term memory (Lab 3 · Task 3)

**Goal:** move the agent's short-term memory — the in-progress dispatch plan and the pending
approval — from the in-memory `MemorySaver()` to **Lakebase** so it survives an app restart.

> **Workshop context — each participant uses their OWN Lakebase project.** Everyone shares one
> Databricks workspace, so a single shared Lakebase instance would make every app's service
> principal collide on the same schema names (`agent_memory`, and the chat UI's `ai_chatbot` /
> `drizzle`). The fix is isolation, not permission-granting: each participant creates their **own
> autoscaling Lakebase project**. Their app's service principal is then the sole owner of every
> schema it creates there — no grants, no collisions, and the chat UI's history works too.

> **Deploy is UI-only.** Participants redeploy from the app's page in the workspace (the **Deploy**
> button), never `databricks bundle deploy`. That has one consequence this skill relies on:
> - **Code and `app.yaml`** live in the app source, so edits to them ship on the next UI Deploy. ✅
> - **The Lakebase resource attach is app *configuration*, not source** — it is set in the app's
>   **Edit → App resources** UI (or the Apps API), and is **not** driven by `databricks.yml`.
>   `databricks.yml`'s `resources:` block is only applied by `bundle deploy`, which we do not run,
>   so **do not edit `databricks.yml` to wire Lakebase** — it will silently do nothing.

## What you will change

| Thing | How | Who |
|---|---|---|
| Create an autoscaling Lakebase **project** | `databricks postgres create-project` (or the Lakebase UI) | this skill / participant |
| `agent_server/start_server.py` — swap `MemorySaver` → env-driven `AsyncCheckpointSaver` | file edit | **this skill** |
| `app.yaml` — set `LAKEBASE_AUTOSCALING_PROJECT` / `LAKEBASE_AUTOSCALING_BRANCH` | file edit | **this skill** |
| Attach the project as the app's Lakebase resource | **Edit → App resources** in the UI | participant |
| Deploy | **Deploy** button in the app UI | participant |

---

## Step 1 — Create the participant's own Lakebase project

Pick a name unique to this participant so nobody collides. Derive it from their username:

```bash
USER_NAME=$(databricks current-user me --profile "$PROFILE" | jq -r '.userName' | cut -d@ -f1 | tr '.[:upper:]' '-[:lower:]')
PROJECT="lakebase-${USER_NAME}"          # e.g. lakebase-marc-shreya
databricks postgres create-project "$PROJECT" \
  --json '{"spec": {"display_name": "'"$PROJECT"'"}}' --profile "$PROFILE"
```

This auto-provisions a `production` branch, a `primary` endpoint, and the default
`databricks_postgres` database. Confirm it is `READY`:

```bash
databricks postgres list-branches "projects/${PROJECT}" --profile "$PROFILE"
```

> **No CLI available?** Create it in the UI instead: **Lakebase → Projects → Create project**,
> name it `lakebase-<username>`, and note the project name. Everything below only needs the name.

> **Autoscaling, not Provisioned.** A project you create today is *autoscaling*. Its connection
> form is `project` + `branch` — **never** `instance_name=` (that resolves only legacy Provisioned
> instances and will fail with `Unable to resolve Lakebase provisioned instance`).

## Step 2 — Edit `app.yaml` (point the app at this project)

Add these two env vars under `env:` in `app.yaml` (the backend reads them; they ship on Deploy
because `app.yaml` is part of the app source):

```yaml
  - name: LAKEBASE_AUTOSCALING_PROJECT
    value: "lakebase-<username>"     # the project created in Step 1
  - name: LAKEBASE_AUTOSCALING_BRANCH
    value: "production"
```

## Step 3 — Edit `agent_server/start_server.py` (the one code change)

Add this block right after `app = agent_server.app`. It swaps the in-memory `MemorySaver` for a
Lakebase-backed `AsyncCheckpointSaver`, connected **from the env vars** (so each participant hits
their own project), and rebinds the dispatch graph to it:

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
    # Deployed: durable short-term memory on THIS PARTICIPANT'S OWN autoscaling Lakebase project.
    # Connection is env-driven (set in app.yaml) — autoscaling projects use project/branch, never
    # instance_name. Because the project is the participant's own, the app SP creates and owns the
    # `agent_memory` schema here; no grants, no collisions.
    async with AsyncCheckpointSaver(
        project=os.environ["LAKEBASE_AUTOSCALING_PROJECT"],
        branch=os.environ.get("LAKEBASE_AUTOSCALING_BRANCH", "production"),
        schema="agent_memory",
    ) as checkpointer:
        await checkpointer.setup()                           # REQUIRED — creates the tables
        dispatch.GRAPH = dispatch.build_graph(checkpointer)  # rebind the dispatch agent to Lakebase memory
        async with _original_lifespan(app):
            yield


app.router.lifespan_context = _lifespan
```

Three things that MUST be right, or it fails silently:
1. **`project=` / `branch=`, not `instance_name=`.** Autoscaling projects are resolved by
   project/branch. `instance_name=` calls the Provisioned API and raises `NotFound`.
2. **`await checkpointer.setup()`** creates the `checkpoints` / `checkpoint_writes` tables. Skip it
   and the first request errors with `relation "checkpoints" does not exist`.
3. **Enter with `async with`** — that opens the connection pool. Never build a bare singleton.

The `dispatch.build_graph(checkpointer)` line — the custom dispatch agent and its approval gate —
is unchanged. Do **not** edit `dispatch.py`, the graph nodes, or the approval gate.

## Step 4 — Attach the project as the app's Lakebase resource (UI)

The **chat UI** (the bundled `e2e-chatbot-app-next` frontend) gets its Postgres connection from the
app's attached resource, not from code. Point it at the participant's project — in the app UI:

> **Edit → App resources → Add/Edit resource → Database → project `lakebase-<username>`,
> branch `production` → permission `CAN_CONNECT_AND_CREATE` → Save.**

- This is a **UI action** (or Apps API), not a file edit — `databricks.yml` will not do it on a UI
  deploy. If a resource is already attached to the old shared instance, **re-point it** to this
  project.
- Permission must be `CAN_CONNECT_AND_CREATE` — the frontend creates its own `ai_chatbot` /
  `drizzle` schemas on first start; with only `CAN_CONNECT` it crashes with `permission denied`.

## Step 5 — Deploy (UI) and verify

> **Deploy from the app's page in the workspace — click Deploy, wait for Running.** Do **not** run
> any CLI / `databricks bundle deploy`.

On first start the app's service principal creates and owns every schema in the participant's own
project: `agent_memory` (checkpointer) plus `ai_chatbot` + `drizzle` (chat UI). No grants needed.

Then confirm durable memory end-to-end:
1. Open the app → chat **"Build my dispatch plan"**.
2. **Restart the app.**
3. Chat **"approve CBM-003"** — it still works, because the plan and pending approval were read
   back from Lakebase, not memory.

To eyeball it: in your project's **Tables**, the `agent_memory` schema holds `checkpoints` /
`checkpoint_writes` / `checkpoint_migrations`, all owned by the app's service principal.

## If it still crashes

| Symptom | Cause | Fix |
|---|---|---|
| `Unable to resolve Lakebase provisioned instance` | Used `instance_name=` on an autoscaling project | Use `project=` / `branch=` (Step 3) |
| `permission denied for schema/table …` | App is pointed at the **shared** instance (another SP owns the schema) | Re-point BOTH the `app.yaml` env (Step 2) and the UI resource (Step 4) to the participant's own project |
| Chat UI dies, backend fine ("both processes") | The UI resource still points at the old instance | Re-point the resource in the UI (Step 4) |
| `relation "checkpoints" does not exist` | Missing `await checkpointer.setup()` | Add it (Step 3) |
