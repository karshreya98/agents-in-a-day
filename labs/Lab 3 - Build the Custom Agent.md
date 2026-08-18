# 🤖 Lab 3 — Build Marc's Custom Agent, then Observe & Review It

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- Explain **when to graduate from Genie One to a custom agent** — and what you gain:
  a wider tool palette and, above all, **control flow you own**.
- Deploy a **custom agent as a Databricks App** — a React chat UI + FastAPI backend
  with the agent's logic running inside it.
- Recognise the agent's **explicit control-flow pipeline**: assess → quantify → enrich →
  rank → assign → draft → **gated write-back**.
- Inspect the agent's **MLflow traces** to see every step and tool call.
- Create a **label schema** and launch a **Review App** so domain experts grade real
  answers, with feedback attached back to each trace.

## Introduction

Marc is the **operations manager** at Sunny Bay Roastery. He doesn't drive to machines —
he runs the 12 locations and the 12 location managers behind them (Sara, from Lab 1,
manages Mission). His job is **prioritisation and coordination**: which machines threaten
which stores, who to dispatch, and who to tell.

In Labs 1–2 you *configured* Genie — no code, best-effort, brilliant for exploration.
Genie One already routes across your data, Genie agents, and the web. So why build
anything else?

> [!NOTE]
> **This is a graduation, not a criticism of Genie One.** Marc can get a long way in
> Genie One + Skills. You reach for a **custom agent** when you want a *wider set of
> tools* under *flow you control and can test* — and you keep Unity Catalog governance,
> MLflow tracing, and the Review App the whole way.

| | Genie One (+ Skills) | Custom agent (this lab) |
|---|---|---|
| Data assets, Genie agents, MCP (web) | ✅ | ✅ |
| **Unity Catalog functions** as first-class tools (write-back) | limited | ✅ |
| **Custom Python** (scoring, ranking, business rules) | — | ✅ |
| **Control flow** — a deterministic, testable pipeline | best-effort routing | ✅ **you own it** |
| **Human-in-the-loop approval gate** before an action | — | ✅ |
| Your own **app experience** (buttons, cards) | Genie chat UI | ✅ |
| Governance · MLflow traces · Review App | ✅ | ✅ |

> [!NOTE]
> **Why this replaces the old "Supervisor Agent."** Earlier versions of this workshop
> used the managed Multi-Agent Supervisor. It's being **deprecated** — and it hid the
> orchestration from you. A custom agent puts that logic back in your hands as code you
> can read, test, and version.

> [!IMPORTANT]
> **Prerequisites:**
> - Lab 0 setup job has run (`machines`, `fault_reports_structured`, `location_managers`,
>   and the `create_service_order` UC function all exist).
> - The **Sunny Bay Maintenance Genie** (Lab 1) and pre-built **Sunny Bay Sales Genie** exist.
> - you.com MCP service is registered in the Unity AI Gateway (Lab 1 — Step 4b).
> - You have the Databricks CLI (`databricks --version`) and can deploy a **Databricks App**.

---

## What Marc's agent does

The app is a **chat cockpit**. Marc types naturally and the agent **routes his intent** to
the right capability:

| Marc says… | The agent… |
|---|---|
| *"Build my dispatch plan"* | runs the pipeline below and renders ranked cards |
| *"Why is CBM-003 ranked first?"* | explains the score straight from the trace |
| *"What's the weekly revenue by store?"* | routes to a Genie tool and answers |
| *"Approve CBM-003"* | executes the gated `create_service_order` write-back |

The routing is the agent's judgement; the capabilities behind it are deterministic tools.
The flagship one is the dispatch pipeline — an explicit **LangGraph** graph, the control
flow the old Supervisor never let you see:

```
assess → quantify → enrich → score → assign → approval_gate ⇄ execute
                                                 (interrupt)   (create_service_order)

assess         → Maintenance Genie: which machines have unresolved faults?
quantify       → Sales Genie: weekly revenue per store  (→ revenue-at-risk)
enrich [if code] → you.com MCP: manufacturer bulletin for that fault code
score          → plain Python: priority = 4·faults + revenue_at_risk/1000
assign         → location_managers roster: draft a message to the right manager
approval_gate  → LangGraph interrupt — PAUSES here until Marc approves
execute        → create_service_order()  ← resumes only after approval
```

Two things here are impossible in Genie One: the **deterministic scoring/ranking in
Python**, and the **approval gate** — implemented as a **LangGraph interrupt**: the graph
literally pauses before `create_service_order` and only resumes when Marc approves.
Because when *Marc's* agent creates an order, Marc is accountable for it.

> [!NOTE]
> **This uses the canonical Databricks stack**, so what you learn transfers: a **LangGraph**
> graph wrapped in an **MLflow `ResponsesAgent`** (the recommended authoring interface),
> with `mlflow.langchain.autolog()` for tracing — the same pattern as the official
> [`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph)
> template. We add our own React cockpit on top for the manager UX.

---

## Instructions

### **Step 1: Look at the agent's control flow (5 min)**

The app lives in **`app/`** in this repo. Open **`app/server/graph.py`** — the LangGraph
`StateGraph`.

1. Find `build_graph()`. The nodes and edges *are* the control flow — `assess → quantify →
   enrich → score → assign → approval_gate ⇄ execute`. You can read exactly what happens, in
   what order.

2. Find the `score` node and the `FAULT_WEIGHT` / `REVENUE_WEIGHT` constants — **Marc's
   policy as code**, deterministic and testable, not a prompt the model might ignore.

3. Find `approval_gate`. It calls `interrupt(...)` — the graph **pauses** here. `execute`
   (which calls `create_service_order`) only runs when the app resumes the graph with an
   approval. That's the **human-in-the-loop gate**, done the LangGraph way.

4. Open **`app/server/tools.py`** — the tool palette: two Genie spaces, the you.com web
   search, the `create_service_order` **UC function**, and the `location_managers` roster.
   A wider set than Genie One orchestrates directly.

5. Open **`app/server/responses_agent.py`** — the graph wrapped in an MLflow
   `ResponsesAgent`. This is the portable, loggable, deployable surface (serving endpoint,
   Review App, eval). And **`app/server/agent.py`** holds the chat **router** (`chat()` /
   `_route()`) that classifies each message into *plan / explain / qa / approve / help* — so
   the chat is the interface to the workflow, not a generic text-to-SQL box.

> [!TIP]
> One line — `mlflow.langchain.autolog()` — traces every LangGraph node and LLM call
> automatically. That's how each step shows up as a span in the trace you'll inspect in
> Step 4: tracing is built in, not bolted on.

---

### **Step 2: Wire and deploy the app (10 min)**

The app runs the agent **inside itself** — one deploy, no separate serving endpoint
("Pattern B"). Traces still log to MLflow.

1. Get your two **Genie space IDs**. Open each Genie agent; the space ID is in the URL
   (`.../genie/rooms/<SPACE_ID>`). Put them in **`app/app.yaml`**:

   ```yaml
   env:
     - name: CATALOG
       value: "sunny_bay_roastery"        # your Lab 0 catalog
     - name: MAINTENANCE_GENIE_SPACE_ID
       value: "<your maintenance space id>"
     - name: SALES_GENIE_SPACE_ID
       value: "<your sales space id>"
   ```

2. From a terminal in the repo, build the frontend and create the app:

   ```bash
   cd app/frontend && npm install && npm run build && cd ..
   databricks apps create marc-manager-agent
   databricks sync . /Workspace/Users/<you>/marc-manager-agent \
     --exclude node_modules --exclude .venv --exclude frontend/src
   databricks apps deploy marc-manager-agent \
     --source-code-path /Workspace/Users/<you>/marc-manager-agent
   ```

3. In the app's page (**Compute → Apps → marc-manager-agent → Edit**), add resources:
   - a **Model serving endpoint** (a Claude/Llama Foundation Model) → *Can query*
   - **SQL warehouse** access so the UC function and roster query can run

   Redeploy to pick up the env vars.

> [!TIP]
> **Want to try it first with zero setup?** The app has an offline mode. Locally, run
> `AGENT_DRY_RUN=1 uv run uvicorn app:app --port 8000` from `app/` — it serves the same UI
> with canned Sunny Bay data, no workspace calls. Great for seeing the flow before you wire
> the real Genie spaces.

---

### **Step 3: Use the agent (5 min)**

Open the app URL — it's a chat. Work through the four things it can do (type them, or click
the suggestion chips):

1. **"Build my dispatch plan."** The agent runs its pipeline and returns **ranked machine
   cards**. **CBM-003 (Mission)** should sit at the top — 3 unresolved E-07 faults and high
   store revenue give it the highest priority score. On a flagged card, read the **draft
   message** to that location's manager (Sara, for Mission) and the **manufacturer
   bulletin** it pulled from the web.

2. **"Why is CBM-003 ranked first?"** The agent explains the score — the fault points plus
   the revenue-at-risk points — straight from its own deterministic formula.

3. **"What's the weekly revenue by store?"** A data question — the agent routes it to the
   Sales Genie and answers.

4. **"Approve CBM-003"** (or click **Approve & create service order** on the card). *Now* —
   and only now — the agent calls the `create_service_order` UC function and returns the new
   order ID.

> [!NOTE]
> Nothing was written until you approved. That gate is the difference between an
> assistant that *answers* and an agent Marc trusts to *act*. Notice too how the agent
> **chose** a different capability for each message — that routing is its judgement; the
> capabilities behind it are governed, deterministic tools.

---

### **Step 4: Inspect the MLflow traces (8 min)**

Every message the agent handles is logged as an **MLflow trace** — a full record of the
routing and every tool call. Because you asked four *different* things in Step 3, you'll
have four *different-shaped* traces to inspect (a plan, an explanation, a Genie lookup, an
approval) — not five copies of the same one.

1. In the workspace sidebar open **Experiments** (under **Machine Learning** / **MLflow**).

2. Open the experiment named in `app.yaml`'s `MLFLOW_EXPERIMENT` (default
   **`/Shared/marc-manager-agent`**).

3. Click the **Traces** tab. Each interaction is one row. Open a dispatch-plan trace and
   explore the **span waterfall** — one span per LangGraph node: `assess` (Maintenance
   Genie) → `quantify` (Sales Genie) → `enrich` (you.com) → `score` → `assign` →
   `approval_gate`.

4. Click into a span to see its exact inputs and outputs — e.g. what the Maintenance
   Genie returned, or the priority score the Python step computed.

> [!NOTE]
> This is how you debug an agent. If a plan missed a machine, the trace shows *which step*
> dropped it — you're never guessing. Because the flow is explicit, the trace reads like
> the code.

---

### **Step 5: Create a label schema (5 min)**

A **label schema** is the question set your domain experts answer for each trace, so
feedback stays consistent.

1. In your experiment, open the **Labeling** area → **Labeling schemas** → **Create schema**.

2. A quality rating:

   | Field | Value |
   |---|---|
   | **Name** | `plan_quality` |
   | **Type** | Feedback · Categorical |
   | **Options** | `Poor`, `Fair`, `Good`, `Excellent` |
   | **Instruction** | `As the manager receiving this dispatch plan, is the ranking sensible and are the drafted messages ready to send?` |
   | **Enable comment** | ✅ On |

3. A hard correctness check:

   | Field | Value |
   |---|---|
   | **Name** | `grounded_in_data` |
   | **Type** | Feedback · Categorical |
   | **Options** | `Yes`, `No` |
   | **Instruction** | `Are the fault counts, revenue figures, and part numbers all supported by Sunny Bay's data — nothing made up?` |

---

### **Step 6: Launch a labeling session and Review App (7 min)**

A **labeling session** bundles traces with your schemas and hands reviewers a friendly
**Review App** — no Databricks skills needed.

1. **Labeling** area → **Labeling sessions** → **Create labeling session**.

   | Field | Value |
   |---|---|
   | **Name** | `Sunny Bay — Dispatch Plan Review` |
   | **Label schemas** | `plan_quality` and `grounded_in_data` |
   | **Assigned users** | your domain experts (e.g. a colleague, or Marc/Sara) |

2. From the **Traces** tab, select the traces from Step 3/4 → **Add to labeling session** →
   your new session.

3. Open the session → **Share** → copy the **Review App URL** and send it to your reviewers.

4. Open the Review App yourself: it shows one plan at a time with your schema questions on
   the side. Rate it, add a comment, submit.

5. Back in **Traces**, open a labeled trace — your feedback now appears under
   **Assessments**, attached to that exact trace.

> [!NOTE]
> This is the loop that hardens an agent: real experts grade real output through a simple
> UI, and every rating lands on the trace. That labeled feedback is what you'd later use to
> build an evaluation set or align an automated judge — so quality checks run continuously.

---

## 💡 Key takeaways

- **Custom agent = control you own.** The pipeline is ordered Python you can read, test,
  and version — not best-effort routing.
- **A wider tool palette** — Genie spaces *and* a UC write-back function *and* custom
  Python scoring, composed together.
- **The approval gate** is the line between answering and acting. It's why Marc trusts the
  agent with `create_service_order`.
- **You lose nothing by going custom** — governance, MLflow traces, and the Review App all
  still apply.
- **When to graduate:** stay in Genie One for exploration; reach for a custom agent when
  you need actions, guaranteed behaviour, or your own app experience.

---

## What Happens Next?

Marc has a custom agent — deployed as an app, observable in MLflow, and reviewed by the
people who do the job. In the final lab you meet the **Unity AI Gateway** head-on and see
how the platform governs the AI *coding* that produced the write-back function.

➡️ Continue to **[Lab 4 — AI Gateway and Write-back](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
