# Databricks notebook source
# MAGIC %md
# MAGIC # 🔬 Explore the dispatch agent's traces
# MAGIC
# MAGIC Runs Marc's dispatch agent (from Lab 3) **inside this notebook** and records each message
# MAGIC as an MLflow trace you can open, drill into, and add to a labeling session — the full
# MAGIC **span waterfall**, on **any** workspace including Free Edition.
# MAGIC
# MAGIC *(A deployed app on Free Edition can't store span data — see the
# MAGIC [Observability & Feedback](./Observability%20and%20Feedback.md) deep dive. A notebook can,
# MAGIC which is why we trace from here.)*
# MAGIC
# MAGIC **To run:** set `APP_DIR` in Cmd 3 to your Git-folder `app/` path, then **Run All**.

# COMMAND ----------

# MAGIC %pip install -q "mlflow>=3.10" "langgraph>=1.1.0" nest_asyncio
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import os, sys, asyncio, mlflow

os.environ["AGENT_DRY_RUN"] = "1"   # canned Sunny Bay data — no Genie/warehouse needed
# (Leave MLFLOW_TRACE_CATALOG / MLFLOW_TRACE_SCHEMA unset: from a notebook the default trace
#  store works, so we don't need Unity Catalog trace storage.)

mlflow.set_experiment("/Shared/dispatch-agent-observability")

# 👇👇👇 PASTE YOUR GIT-FOLDER app/ PATH HERE (e.g. /Workspace/Users/you@example.com/agents-in-a-day/app)
APP_DIR = "/Workspace/Users/<you>@example.com/agents-in-a-day/app"
# 👆👆👆
sys.path.insert(0, APP_DIR)

from agent_server import dispatch   # the LangGraph pipeline — light, no server deps
print("dispatch imported from", APP_DIR)

# COMMAND ----------

# Databricks notebooks already run inside an event loop, so allow nesting before asyncio.run:
import nest_asyncio
nest_asyncio.apply()

# A root AGENT span per message, mirroring the deployed app's build_reply — the graph nodes
# and tool calls nest underneath it into one trace.
@mlflow.trace(span_type="AGENT", name="dispatch_agent")
async def dispatch_agent(text, thread="observability-lab"):
    t = text.lower()
    if "approve" in t:
        return dispatch.format_order(await dispatch.approve_machine(thread, text))
    if t.startswith("why") or "explain" in t:
        return await dispatch.explain_ranking(thread, text)
    return dispatch.format_plan(await dispatch.build_plan(thread))

async def go():
    print(await dispatch_agent("Build my dispatch plan")); print("---")
    print(await dispatch_agent("Why is CBM-003 ranked first?")); print("---")
    print(await dispatch_agent("approve CBM-003"))

asyncio.run(go())
mlflow.flush_trace_async_logging()
print("\ntraces flushed")

# COMMAND ----------

# Confirm the span tree landed (before opening the UI)
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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next
# MAGIC
# MAGIC 1. Sidebar → **Experiments** → **`/Shared/dispatch-agent-observability`** → **Traces** →
# MAGIC    open the **"Build my dispatch plan"** trace → **See detailed trace view** and walk the
# MAGIC    waterfall (`dispatch_agent → assess → Genie tools → score → approval_gate`).
# MAGIC 2. Build the feedback loop (labeling schemas + Review App) — see **Part 3** of the
# MAGIC    [Observability & Feedback](./Observability%20and%20Feedback.md) deep dive.
