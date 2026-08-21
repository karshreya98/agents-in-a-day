# 🤖 Lab 3 — Build & Deploy Marc's Custom Agent

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- **Create a custom agent app** on Databricks from the Apps UI.
- Read the agent's source code and find **where the control flow is defined**.
- Use the in-product **AI assistant to add a Databricks capability** — durable **short-term
  agent memory backed by Lakebase** — without writing the code yourself.
- **Observe and review** the agent with **MLflow traces** and a **Review App**.

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
assess → score → approval_gate ⇄ execute
                   (interrupt)   (create_service_order)

assess        → the Genies: which machines have unresolved faults, and each store's revenue
score         → plain Python: priority = 4·faults + revenue_at_risk/1000, then draft messages
approval_gate → LangGraph interrupt — PAUSES here until Marc approves a machine
execute       → create_service_order()  ← runs only after Marc approves
```

In the chat, the agent returns the result as a **ranked plan**: for each machine, its
location, the fault count and code, the revenue at risk, the priority score, and the
**draft message** to that store's manager. **The plan writes nothing.**
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

### **Task 1: Create the app in the UI (10 min)**

A custom agent is just an app you deploy on Databricks. Let's stand this one up first.

1. **Get the code into your workspace** (if it isn't already): sidebar → **Workspace →
   Create → Git folder**, paste this repo's URL, **Create**. The app lives in the `app/`
   folder (that's where `app.yaml` is).

2. **Create the app**: **Compute → Apps → Create app → Custom**, name it
   `marc-dispatch-agent`, **Create**.

3. **Deploy it**: open the app → **Deploy** → set the source path to the `app/` folder →
   **Deploy**, and wait for **Running**.

The app ships in **sample-data mode**, so it deploys with **no resources to attach**. Open
the app URL and try it — it's a chat cockpit:

| You say… | The agent… |
|---|---|
| **"Build my dispatch plan"** | ranks this week's machines and returns the plan |
| **"Why is CBM-003 ranked first?"** | explains the score from its own formula |
| **"Approve CBM-003"** | runs the gated `create_service_order` write-back |

Reply **"approve CBM-003"** and the agent raises the order — but only *after* your approval.

---

### **Task 2: Find where the control flow is defined (5 min)**

Open **`app/agent_server/dispatch.py`** — this is the agent's brain. Two things to spot:

1. **`build_graph()`** — the four nodes and edges *are* the control flow:
   `assess → score → approval_gate ⇄ execute`. The `approval_gate` node calls
   `interrupt(...)`, which pauses the graph until your "approve" resumes it.

2. **`build_checkpointer()`** — this is the agent's **short-term memory**: where the
   in-progress plan and the pending approval are stored between your messages. Right now
   it's `MemorySaver()` — **in-memory**, so if the app restarts, the plan and pending
   approval are **gone**. That's what you'll fix in Task 3.

---

### **Task 3: Add short-term memory with Lakebase — using the AI assistant (15 min)**

You won't hand-write this. You'll provision a **Lakebase** instance (Databricks' managed
Postgres) and let the in-product **AI assistant** make the code change for you.

1. **Create a Lakebase instance**: sidebar → **Compute → Database instances → Create
   database instance** (Lakebase). Give it a name and create it. Note its name/endpoint —
   you'll grant your app access to it.

2. **Open the app's code** in the workspace editor, open the **AI assistant**, and give it
   this prompt:

   > *"Add short-term agent memory to this app backed by Lakebase, following the
   > `add-lakebase-short-term-memory` skill. Replace the in-memory `MemorySaver()` in
   > `agent_server/dispatch.py` with a Lakebase-backed `AsyncCheckpointSaver` so the
   > dispatch plan and the pending approval survive an app restart. Add the
   > `databricks-langchain[memory]` dependency, add my Lakebase instance as an app resource,
   > and initialize the checkpoint tables once at startup. Don't change the graph nodes or
   > the approval gate."*

   The assistant follows the bundled **`add-lakebase-short-term-memory`** skill (in
   `app/.claude/skills/`) to make the edits.

3. **Redeploy** the app (Task 1, step 3) and let it reach **Running**.

4. **Prove the memory is durable**: ask **"Build my dispatch plan"**, then **restart the
   app** from its page. When it's back, reply **"approve CBM-003"** — it *still works*,
   because the plan and pending approval were read back from **Lakebase**, not memory.

> [!NOTE]
> That's the whole point: **durable agent memory on governed Postgres you didn't have to
> run.** The pattern is short-term (thread-scoped) memory — the same one the
> [`agent-langgraph-advanced`](https://github.com/databricks/app-templates/tree/main/agent-langgraph-advanced)
> template ships.

---

### **Task 4: Observe and review with MLflow (12 min)**

Every message is logged as an **MLflow trace** — the full record of the routing and every
tool call.

1. Sidebar → **Experiments** → open the experiment **linked to your app**. Click the
   **Traces** tab, open a dispatch-plan trace, and explore the **span waterfall** — one span
   per LangGraph node: `assess` → `score` → `approval_gate`. Click a span to see its exact
   inputs and outputs (what the Genie tool returned, the priority score, the Lakebase
   checkpoint read/write).

2. **Stand up a Review App** so domain experts grade real output:
   - In your experiment: **Labeling → Labeling schemas → Create schema**. Add a
     `plan_quality` rating (*Poor / Fair / Good / Excellent* — "is the ranking sensible and
     are the drafted messages ready to send?") and a `grounded_in_data` check (*Yes / No* —
     "are the fault counts, revenue, and parts all supported by the data?").
   - **Labeling → Labeling sessions → Create labeling session**, name it
     `Sunny Bay — Dispatch Plan Review`, attach both schemas, assign reviewers.
   - From **Traces**, select your traces → **Add to labeling session**.
   - Open the session → **Share** → copy the **Review App URL** for reviewers. Open it
     yourself, rate a plan, submit — the feedback lands back under **Assessments** on that
     exact trace.

> [!NOTE]
> This is the loop that hardens an agent: the people who do the job grade real output, and
> every rating attaches to the trace — the raw material for an eval set or an automated judge.

---

## 💡 Key takeaways

- **A custom agent is just an app** you create and deploy from the Databricks Apps UI.
- **The control flow lives in code you can read** — an explicit pipeline with a
  human-in-the-loop approval gate before it acts.
- **You extend the agent with Databricks capabilities, by prompting the AI assistant** — you
  added durable **short-term memory on Lakebase** without writing the code yourself.
- **Observability and review are built in** — MLflow traces to debug, and a Review App so
  the people who do the job grade real output.

---

## What Happens Next?

Marc has a custom agent — deployed as an app, observable in MLflow, and reviewed by the
people who do the job. In the final lab you meet the **Unity AI Gateway** head-on and see
how the platform governs the AI *coding* that produced the write-back function.

➡️ Continue to **[Lab 4 — AI Gateway and Write-back](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
