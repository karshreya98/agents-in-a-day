# 🔬 Deep Dive — Observability & Feedback

> A deep dive that pairs with **[Lab 3 — Build the Custom Agent](../Lab%203%20-%20Build%20the%20Custom%20Agent.md)**.
> Do Lab 3 first (you'll have Marc's dispatch agent running); come here to see *inside* it and
> to build the loop that hardens it over time.

## 🎯 What you'll learn

- **Read an agent's MLflow trace** — the span waterfall that shows the routing, every
  LangGraph node, and every tool call, with the exact inputs and outputs.
- **Where traces are stored**, and the one thing that differs between **Free Edition** and a
  **paid / managed-storage** workspace (so you're never surprised by an empty trace).
- **Collect expert feedback** with a **Review App** and labeling sessions — the raw material
  for an eval set or an automated judge.

---

## ⚠️ Read this first: Free Edition vs. paid workspaces

An MLflow trace has two parts: the **trace record** (the request, the response, latency,
status — lightweight, saved through the workspace API) and the **span data** (the waterfall:
each node and tool call with its inputs/outputs — heavier, written to storage).

Where the span data can be written depends on **who is producing the trace** and **what
storage the workspace has**:

| Producing the trace from… | Free Edition | Paid / managed-storage workspace |
|---|---|---|
| **A notebook or an eval run** (this lab's main path) | ✅ full waterfall | ✅ full waterfall |
| **A deployed Databricks App** | ⚠️ trace record only — **no span waterfall** | ✅ full waterfall (via Unity Catalog) |

**Why the deployed-app gap on Free Edition?** A deployed app runs in a locked-down network
sandbox that can't reach the default trace-artifact storage, so its span data is dropped —
you'll see the message *"No trace data available."* The usual fix, **Unity Catalog trace
storage**, needs *managed* storage, which Free-Edition catalogs don't have. So on Free
Edition, a deployed app's detailed trace stays empty — it's a platform limit, not a bug.

**The good news:** a **notebook** (or an eval) runs in a context that *can* write span data,
on **any** workspace. So this lab drives the agent **from a notebook** — you get the full,
explorable, labelable waterfall on Free Edition *and* paid. Part 4 then shows the production
path (the deployed app streaming live traces to Unity Catalog) for when you're on a
managed-storage workspace.

---

## Part 1 — Generate a full trace from a notebook (works everywhere)

Create a notebook in your workspace (in the same Git folder as the app) and run these cells.

**Cell 1 — install the agent's dependencies**
```python
%pip install -q "mlflow>=3.10" "databricks-agents>=1.9.3" "databricks-langchain[memory]" "langgraph>=1.1.0" langchain-core python-dotenv
dbutils.library.restartPython()
```

**Cell 2 — point MLflow at an experiment and import the agent**
```python
import os, sys, asyncio, mlflow

os.environ["AGENT_DRY_RUN"] = "1"   # canned Sunny Bay data — no Genie/warehouse needed
# Leave MLFLOW_TRACE_CATALOG / MLFLOW_TRACE_SCHEMA UNSET here: from a notebook the default
# (managed) trace store works, so we don't need Unity Catalog trace storage.

mlflow.set_experiment("/Shared/dispatch-agent-observability")

# Make the app package importable — EDIT to your Git folder's app/ path:
APP_DIR = "/Workspace/Users/<you>@example.com/agents-in-a-day/app"
sys.path.insert(0, APP_DIR)

from agent_server import agent
from mlflow.types.responses import ResponsesAgentRequest
print("agent imported")
```

**Cell 3 — drive the agent (this is what records the traces)**
```python
def ask(text):
    return ResponsesAgentRequest(
        input=[{"role": "user", "content": text}],
        custom_inputs={"user_id": "observability-lab"},
    )

async def go():
    print(await agent.build_reply(ask("Build my dispatch plan")))
    print("---")
    print(await agent.build_reply(ask("Why is CBM-003 ranked first?")))
    print("---")
    print(await agent.build_reply(ask("approve CBM-003")))

asyncio.run(go())          # if this errors "running event loop":
                           #   %pip install nest_asyncio → import nest_asyncio; nest_asyncio.apply()
mlflow.flush_trace_async_logging()
print("traces flushed")
```

**Cell 4 — confirm the span tree landed (before opening the UI)**
```python
import time; time.sleep(3)
t = max(mlflow.search_traces(max_results=8, return_type="list"), key=lambda x: len(x.data.spans))
kids = {}
for s in t.data.spans:
    kids.setdefault(s.parent_id, []).append(s)
def show(pid, d):
    for s in sorted(kids.get(pid, []), key=lambda x: x.start_time_ns):
        print("  " * d + f"- [{s.span_type}] {s.name}")
        show(s.span_id, d + 1)
print(f"{len(t.data.spans)} spans:")
show(None, 0)
```

You should see one connected tree per message, e.g. for the plan:

```
- [AGENT] dispatch_agent
  - [CHAIN] assess
    - [TOOL] ask                 (Maintenance Genie)
    - [TOOL] ask                 (Sales Genie)
    - [TOOL] get_location_roster
  - [CHAIN] score
  - [CHAIN] approval_gate
```

---

## Part 2 — Read the trace in the UI

1. Sidebar → **Experiments** → open **`/Shared/dispatch-agent-observability`** → **Traces** tab.
2. Open the **"Build my dispatch plan"** trace → **See detailed trace view**.
3. Walk the **span waterfall** top to bottom — it *is* the agent's control flow:
   - **`dispatch_agent`** — the whole message (root).
   - **`assess`** — expand it: the **Genie tool calls** (`ask`) and the roster lookup, each
     with its exact **inputs and outputs** (click a span). This is where you verify the agent
     asked the Genies the right thing and got sensible data back.
   - **`score`** — the deterministic priority ranking.
   - **`approval_gate`** — where the graph paused for a human.
   For the **approve** message you'll see `execute → create_service_order` — the gated
   write-back, captured with the order it raised.
4. Notice each span's **latency** and **status** — this is how you debug a slow or wrong
   answer: you can see exactly which node or tool call caused it.

> [!NOTE]
> This is why a custom agent beats a black-box chatbot: the trace is a faithful, replayable
> record of *what the agent did and why* — every routing decision, every tool result.

---

## Part 3 — Collect expert feedback (the Review App)

Traces tell you *what happened*; feedback tells you *whether it was any good*. The people who
do the job — Marc, the store managers — grade real output, and every rating attaches to the
trace.

1. In the experiment: **Labeling → Labeling schemas → Create schema**. Add:
   - `plan_quality` — a rating (*Poor / Fair / Good / Excellent*): *"is the ranking sensible
     and are the drafted messages ready to send?"*
   - `grounded_in_data` — a yes/no check: *"are the fault counts, revenue, and parts all
     supported by the data?"*
2. **Labeling → Labeling sessions → Create labeling session**, name it
   `Sunny Bay — Dispatch Plan Review`, attach both schemas, assign reviewers.
3. From **Traces**, select the traces you generated in Part 1 → **Add to labeling session**.
4. Open the session → **Share** → copy the **Review App URL** for reviewers. Open it
   yourself, rate a plan, submit — the feedback lands back under **Assessments** on that exact
   trace.

> [!NOTE]
> This is the loop that hardens an agent: real output, graded by the people who own the
> outcome, attached to the exact trace. That labeled set becomes your **eval dataset** and the
> seed for an **automated judge** — so the next version can be measured, not guessed at.

---

## Part 4 — Production: the deployed app's live traces (paid / managed-storage only)

Part 1 traced the agent from a notebook so it works anywhere. In production you want the
**deployed app** to stream traces from *real usage* into an experiment automatically. On a
**managed-storage workspace**, route those traces to **Unity Catalog** so span data lands over
the API (bypassing the app-sandbox storage limit) — and it's queryable from SQL, notebooks,
and dashboards, with UC governance.

The app is already wired for this — `app.yaml` sets the experiment and the UC trace
destination:

```yaml
- name: MLFLOW_EXPERIMENT_NAME
  value: "/Shared/marc-dispatch-agent"
- name: MLFLOW_TRACE_CATALOG
  value: "sunny_bay_roastery"
- name: MLFLOW_TRACE_SCHEMA
  value: "gold"
```

The only manual step is a one-time grant, because the app writes as its **service principal**,
which needs to create/write the trace tables. On the app's page copy its **App ID** (under
*About the App*), then run once in a SQL editor **before the app's first deploy** (UC links the
experiment to storage on startup, and only on an experiment that has no traces yet):

```sql
GRANT USE CATALOG ON CATALOG sunny_bay_roastery TO `<APP_ID>`;
GRANT USE SCHEMA, CREATE TABLE, MODIFY, SELECT ON SCHEMA sunny_bay_roastery.gold TO `<APP_ID>`;
```

Deploy the app, chat with it, and its traces appear in `/Shared/marc-dispatch-agent` with the
same waterfall you explored in Part 2 — now from live traffic, and labelable exactly as in
Part 3.

> [!IMPORTANT]
> On **Free Edition** this step won't take — its catalogs use *default storage*, which can't
> hold UC trace tables, and the deployed app can't reach the default trace store either. That's
> expected. Use the **notebook path (Parts 1–3)** on Free Edition; it gives you the full
> observability and feedback experience without a managed-storage workspace.

---

## 💡 Key takeaways

- **A trace is the agent's control flow, replayable** — root → nodes → tool calls, each with
  inputs, outputs, latency, and status. It's how you debug and trust a custom agent.
- **Where span data can be written depends on the producer and the workspace** — notebooks and
  evals work everywhere; a deployed app needs managed storage (Unity Catalog) for its spans,
  which Free Edition doesn't have.
- **Feedback closes the loop** — expert ratings attached to real traces become the eval set and
  the judge that let you improve the agent with evidence, not guesswork.
