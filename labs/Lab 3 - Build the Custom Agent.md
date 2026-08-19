# 🤖 Lab 3 — Build & Deploy Marc's Custom Agent

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- See how a **custom agent** is packaged as a **Databricks App** — and that you can start
  one by cloning a template right from the Apps UI.
- Read and **modify the agent's control-flow code** (a LangGraph pipeline) and see your
  change take effect.
- **Deploy** the agent as an App and drive it — including a **human-in-the-loop approval
  gate** before it writes anything back.
- Inspect the agent's **MLflow trace** to debug what it did, step by step.
- Stand up a **Review App** so the people who do the job can grade real answers.

---

## 📖 Introduction

Sara manages one store. **Marc runs all 12.**

Labs 1–2 gave Marc the raw signal he needs, but not the decision:

- **Sara's Maintenance Genie (Lab 1)** — the governed, natural-language way to ask the
  machine/fault data *"which machines have unresolved faults, and what are the codes?"*
- **The field technicians' fault reports (Lab 2)** — the PDFs the techs write after a
  visit, turned into clean structured rows by Document Intelligence (`ai_parse_document` +
  `ai_extract`): which machine, which fault code, what happened.

On his own, Marc would still have to read every field report, cross-check each store's
revenue by hand, and decide store-by-store who to send a technician to first — every week,
across twelve locations.

> **What Marc's custom agent is for.** It does that legwork for him. It reads the field
> reports through Sara's Genie to find machines with unresolved faults, weighs each fault
> against the store's **revenue at risk**, and produces a **dispatch plan** — *a ranked
> shortlist of which machines to service this week, each with a draft message to that
> store's manager*. Marc reviews the plan and **approves** the ones worth acting on; only
> then does the agent raise the actual service order. **The manager keeps the judgement;
> the agent does the legwork.**

That last part — *the agent takes an action, but only after a human approves* — is the
thing a chat assistant can't do and why Marc needs a **custom agent**, not just a chatbot.

---

## What the dispatch plan is

The plan is the output of an explicit **LangGraph** pipeline — control flow you can read,
node by node:

```
assess → quantify → enrich → score → assign → approval_gate ⇄ execute
                                                 (interrupt)   (create_service_order)

assess        → Maintenance Genie: which machines have unresolved faults, and their codes?
quantify      → Sales Genie: weekly revenue per store  (→ that store's revenue at risk)
enrich        → you.com MCP: pull the manufacturer bulletin for the fault code
score         → plain Python: priority = 4·faults + revenue_at_risk/1000
assign        → location_managers roster: draft a message to the right store manager
approval_gate → LangGraph interrupt — PAUSES here until Marc approves a machine
execute       → create_service_order()  ← runs only after Marc approves
```

In the chat, the agent returns the result as a **ranked plan**: for each machine, its
location, the fault count and code, the revenue at risk, the priority score, the bulletin
it pulled, and the **draft message** to that store's manager. **The plan writes nothing.**
It is a recommendation until Marc approves a specific machine — which he does by simply
replying **"approve CBM-003"** in the same chat.

> [!NOTE]
> This app is built directly on the official
> [`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph)
> template — same `agent_server/` layout, same MLflow `ResponsesAgent` handlers, same
> built-in chat UI, same `mlflow.langchain.autolog()` tracing. **The only thing we changed
> is the agent itself:** instead of the template's generic tool-calling loop, it runs the
> explicit LangGraph pipeline above, with the approval gate. So what you learn here is the
> real template, not a bespoke fork.

---

## Instructions

### **Step 1: See how a custom agent becomes an App (5 min)**

First, the product motion — where a custom agent app *comes from*.

1. In the workspace sidebar go to **Compute → Apps → Create app**. Choose **Start from a
   template** and open the **LangGraph agent** template in the gallery. Look at what it
   gives you: an `agent_server/` Python backend, a built-in chat UI, `scripts/quickstart`,
   and an `app.yaml`. **You don't need to finish creating it** — the point is to see that a
   custom agent is just an app you scaffold from this template.

2. Now open **`app/`** in this repo — it *is* that template, with Marc's agent dropped into
   it. Skim the layout so you know where things live:

   | File | What it is |
   |---|---|
   | `app/agent_server/dispatch.py` | The **LangGraph pipeline** — the agent's control flow + scoring policy (Step 2). |
   | `app/agent_server/tools.py` | The **tool palette**: the two Genie spaces, you.com web search, the `create_service_order` UC function, the `location_managers` roster. |
   | `app/agent_server/agent.py` | The template's `ResponsesAgent` handlers, routing each message into *plan / explain / qa / approve*. |
   | `app/agent_server/start_server.py`, `utils.py`, `scripts/` | **Unchanged from the template** — the server, streaming, and quickstart. |
   | `app/app.yaml` | Config + resources (catalog, Genie space IDs, serving endpoint). |

> [!TIP]
> **Want to try it before you deploy?** From `app/`, run `uv sync` then
> `AGENT_DRY_RUN=1 uv run start-server` — the built-in chat UI with canned Sunny Bay data
> and no workspace calls. Great for seeing the flow first.

---

### **Step 2: Explore and modify the flow code (10 min)**

Open **`app/agent_server/dispatch.py`** — this *is* the agent's brain, and unlike
best-effort routing you can read exactly what happens, in what order.

1. Find `build_graph()`. The nodes and edges are the pipeline from the diagram above:
   `assess → quantify → enrich → score → assign → approval_gate ⇄ execute`.

2. Find the `approval_gate` node. It calls `interrupt(...)` — the graph **pauses** here.
   `execute` (which calls `create_service_order`) only runs when the app resumes the graph
   with an approval (that's what your "approve CBM-003" reply does). That's the
   **human-in-the-loop gate**, done the LangGraph way.

3. Find the **scoring policy** near the top of the file — marked `LAB 3 · TASK 2`:

   ```python
   FAULT_WEIGHT = 4.0        # points per unresolved fault
   REVENUE_WEIGHT = 1.0      # points per $1,000/wk of revenue at risk
   DISPATCH_THRESHOLD = 10.0 # a machine must score at least this to make the plan
   ```

   **This is Marc's policy as code** — deterministic and testable, not a prompt the model
   might ignore. Change one value (e.g. bump `REVENUE_WEIGHT` to `2.0`, so a busy store
   outranks a fault-heavy quiet one), save the file, and note what you expect to change in
   the ranking. You'll see the effect when you drive the app in Step 3.

> [!TIP]
> Run `AGENT_DRY_RUN=1 uv run pytest tests/ -q` from `app/` after your edit to confirm the
> pipeline still runs — this is the "testable control flow" a chatbot can't give you.

---

### **Step 3: Deploy the agent as an App and drive it (12 min)**

1. Put your catalog and the two **Genie space IDs** into **`app/app.yaml`** (the space ID
   is in each Genie agent's URL — `.../genie/rooms/<SPACE_ID>`):

   ```yaml
   env:
     - name: CATALOG
       value: "sunny_bay_roastery"          # your Lab 0 catalog
     - name: MAINTENANCE_GENIE_SPACE_ID
       value: "<your maintenance space id>"
     - name: SALES_GENIE_SPACE_ID
       value: "<your sales space id>"
   ```

2. From `app/`, let the template's **quickstart** verify tooling, set up auth, link an
   MLflow experiment, and run it — then deploy with the Databricks CLI (the app serves the
   agent and its chat UI together — one deploy, no separate serving endpoint):

   ```bash
   cd app
   uv run quickstart                       # tooling + auth + MLflow experiment + local run
   databricks apps create marc-dispatch-agent
   databricks sync . /Workspace/Users/<you>/marc-dispatch-agent --exclude .venv
   databricks apps deploy marc-dispatch-agent \
     --source-code-path /Workspace/Users/<you>/marc-dispatch-agent
   ```

3. In the app's page (**Compute → Apps → marc-dispatch-agent → Edit**), add **resources**,
   then redeploy to pick them up:
   - a **Model serving endpoint** (a Claude/Llama Foundation Model) → *Can query*
   - **SQL warehouse** access so the UC function and the roster query can run

4. Open the app URL — it's the template's chat UI. Work through what the agent can do:

   | You say… | The agent… |
   |---|---|
   | **"Build my dispatch plan"** | runs the pipeline and returns the **ranked plan** |
   | **"Why is CBM-003 ranked first?"** | explains the score straight from its own formula |
   | **"What's the weekly revenue by store?"** | routes to the Sales Genie and answers |
   | **"Approve CBM-003"** | executes the gated `create_service_order` write-back |

   On the plan, check that the ranking reflects the weight you changed in Step 2, and read a
   flagged machine's **draft message** (Sara, for Mission) and the **manufacturer bulletin**
   it pulled. Then reply **"approve CBM-003"** — *now*, and only now, the agent resumes past
   the gate, creates the service order, and returns the new order ID.

> [!NOTE]
> Nothing was written until you approved. That gate is the difference between an assistant
> that *answers* and an agent Marc trusts to *act*.

---

### **Step 4: Inspect the MLflow trace (7 min)**

Every message the agent handles is logged as an **MLflow trace** — the full record of the
routing and every tool call. Because you asked several *different* things in Step 3, you
have several *different-shaped* traces to inspect.

1. In the sidebar open **Experiments** (under **Machine Learning** / **MLflow**), and open
   the experiment **`uv run quickstart` created and linked to the app** (the template wires
   it via `app.yaml`'s `MLFLOW_EXPERIMENT_ID`).

2. Click the **Traces** tab. Open a dispatch-plan trace and explore the **span waterfall** —
   one span per LangGraph node: `assess` (Maintenance Genie) → `quantify` (Sales Genie) →
   `enrich` (you.com) → `score` → `assign` → `approval_gate`.

3. Click into a span to see its exact inputs and outputs — e.g. what the Maintenance Genie
   returned, or the priority score the Python step computed.

> [!NOTE]
> This is how you debug an agent. If a plan missed a machine, the trace shows *which step*
> dropped it — you're never guessing. Because the flow is explicit, the trace reads like
> the code you edited in Step 2.

---

### **Step 5: Stand up a Review App (11 min)**

The loop that hardens an agent: real experts grade real output through a simple UI, and
every rating lands back on the trace.

1. **Create a label schema** — the question set your reviewers answer for each trace. In
   your experiment open **Labeling → Labeling schemas → Create schema**, and add two:

   | Field | Quality rating | Correctness check |
   |---|---|---|
   | **Name** | `plan_quality` | `grounded_in_data` |
   | **Type** | Feedback · Categorical | Feedback · Categorical |
   | **Options** | `Poor`, `Fair`, `Good`, `Excellent` | `Yes`, `No` |
   | **Instruction** | *As the manager receiving this plan, is the ranking sensible and are the drafted messages ready to send?* | *Are the fault counts, revenue figures, and part numbers all supported by the data — nothing made up?* |

2. **Create a labeling session** — **Labeling → Labeling sessions → Create labeling
   session**. Name it `Sunny Bay — Dispatch Plan Review`, attach both schemas, and assign
   your reviewers (a colleague, or Marc/Sara).

3. From the **Traces** tab, select the traces from Step 3/4 → **Add to labeling session** →
   your session.

4. Open the session → **Share** → copy the **Review App URL** and send it to reviewers.
   Then open it yourself: it shows one plan at a time with your schema questions on the
   side. Rate it, add a comment, submit.

5. Back in **Traces**, open a labeled trace — your feedback now appears under
   **Assessments**, attached to that exact trace.

> [!NOTE]
> That labeled feedback is what you'd later use to build an evaluation set or align an
> automated judge — so quality checks can run continuously, not just once.

---

## 💡 Key takeaways

- **A custom agent is an app you can scaffold from a template** — a chat frontend, a Python
  backend, and the agent's logic running inside it.
- **The control flow is code you own.** The dispatch pipeline is ordered Python you can
  read, modify, and test — you changed a scoring weight and saw the ranking move.
- **The approval gate is the line between answering and acting.** It's a LangGraph
  `interrupt`, and it's why Marc trusts the agent with `create_service_order`.
- **The trace reads like the code.** One span per node means you debug by looking, not
  guessing.
- **The Review App closes the loop** — the people who do the job grade real output, and
  every rating lands back on the trace.

---

## What Happens Next?

Marc has a custom agent — deployed as an app, observable in MLflow, and reviewed by the
people who do the job. In the final lab you meet the **Unity AI Gateway** head-on and see
how the platform governs the AI *coding* that produced the write-back function.

➡️ Continue to **[Lab 4 — AI Gateway and Write-back](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
