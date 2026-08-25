# 🤖 Lab 3 - Build & Deploy Marc's Custom Agent

> 📘 Reference: [**Author a custom agent** — Databricks docs](https://docs.databricks.com/aws/en/agents/custom-agents/author-agent)

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- **Create a custom agent app** on Databricks from the Apps UI.
- Read the agent's source code and find **where the control flow is defined**.
- Use **Genie Code** to add durable **short-term memory on Lakebase** — without writing the code yourself.

---

## Key concepts

You'll see these terms throughout the lab. Skim them once, then use this as a glossary if something is new.

| Term | What it means here |
|---|---|
| **Custom agent** | Code you own: a fixed sequence of steps (not a generic chat loop) that can **write back** to data after a human says yes. |
| **Databricks App** | How that code is hosted — a workspace app with a URL, deploy button, and (later) attached resources like Lakebase. |
| **Control flow** | The ordered steps: assess → score → pause for approval → execute. Implemented as a **LangGraph** graph in `dispatch.py`. |
| **Approval gate** | A pause (`interrupt`) so Marc reviews the ranked plan. The agent does **not** create a service order until he replies **approve**. |
| **Write-back** | An action that changes data — here, calling the Unity Catalog function `create_service_order`. |
| **Short-term memory / checkpointer** | Where the in-progress plan lives between chat messages. In-memory (`MemorySaver`) dies on restart; **Lakebase** (managed Postgres) keeps it. |
| **Genie Code** | The in-product coding assistant. You attach a **skill** with `@` so it applies a known change instead of inventing one. |
| **Service principal** | The identity the **app** runs as. Attaching Lakebase as an app resource grants *that* identity permission to connect — not just your user. |
| **AI Gateway** *(Lab 4)* | The control plane for **models and tools**: who can call them, with what rules, and with an audit trail. |
| **Service policies** *(Lab 4)* | Rules on a governed model or MCP tool — for example block certain content, or **ASK** (require a human click) before a web search runs. |

This lab builds and deploys Marc's agent. Lab 4 is where you put **policies** on shared **AI Gateway** blocks so the next agent reuses a governed model and tool instead of each team wiring their own.

---

## 📖 Introduction

Sara manages one store. **Marc runs all 12.** Labs 1–2 gave him the signal (faults + field reports); he still has to decide, every week, **who to send a technician to first**.

**Marc's custom agent** does that work in a fixed pipeline. It asks Sara's Genie which machines have unresolved faults, scores each against **revenue at risk**, and returns a **dispatch plan** (ranked list + a draft message to that store's manager). Marc **approves** the ones worth acting on; only then does the agent **write back** a service order. Marc still decides; the agent runs the steps and waits at the **approval gate**.

That workflow is an explicit **LangGraph** pipeline you can read, node by node:

```
assess → score → approval_gate ⇄ execute
                   (interrupt)   (create_service_order)

assess        → the Genies: unresolved faults, and each store's revenue
score         → plain Python: priority = 4·faults + revenue_at_risk/1000, then draft messages
approval_gate → pauses until Marc approves a machine
execute       → create_service_order() — only after approval
```

In chat, **"Build my dispatch plan"** returns the ranked plan. **The plan writes nothing.** Replying **"approve CBM-003"** is what runs the gated write-back. Memory is keyed *per signed-in user* (you'll prove that in Tasks 2–3).

> [!NOTE]
> The app is the official [`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph) template. Same layout, handlers, and chat UI — the only change is this pipeline instead of a generic tool-calling loop.

---

## Instructions

### **Task 1: Create the app in the UI (10 min)**

1. **Get the code into your workspace** (if it isn't already): sidebar → **Workspace → Create → Git folder**, paste this repo's URL, **Create**. The app lives in the `app/` folder (that's where `app.yaml` is).

2. **Create the app**: **Compute → Apps → Create app → Custom**, name it `marc-dispatch-agent`, **Create**.

   <img src="./artifacts/Lab%203/lab_3_task_1_create_custom_app.png" alt="Create a custom app from the Apps UI" width="680">

3. **Deploy it**: open the app → **Deploy** → set the source path to the `app/` folder → **Deploy**, and wait for **Running**.

The app ships in **sample-data mode** — **no resources to attach**. Open the app URL and try the chat:

| You say… | The agent… |
|---|---|
| **"Build my dispatch plan"** | ranks this week's machines and returns the plan |
| **"Why is CBM-003 ranked first?"** | explains the score from its own formula |
| **"Approve CBM-003"** | runs the gated `create_service_order` write-back |

---

### **Task 2: Find where the control flow is defined (5 min)**

On the app's page, click **View source**, then open **`agent_server/dispatch.py`**.

<img src="./artifacts/Lab%203/lab_3_task_2_view_source_code.png" alt="View source on the app page" width="680">

Spot two functions:

1. **`build_graph()`** — the four nodes and edges *are* the pipeline above. `approval_gate` calls `interrupt(...)`, which pauses until your "approve" resumes it.

2. **`build_checkpointer()`** — **short-term memory**: the in-progress plan and pending approval between messages. Right now it's `MemorySaver()` (**in-memory**), so a restart **wipes** them. That's the gap Task 3 closes.

**Prove it forgets (do this before Task 3):** ask **"Build my dispatch plan"**, then **restart the app** from its page. When it's back, reply **"approve CBM-003"** — it answers *"build a plan first"*. Use a **restart**, not a new chat: memory is keyed to you, so it survives chats within a run; only a restart clears `MemorySaver`.

---

### **Task 3: Add short-term memory with Lakebase — using Genie Code (10 min)**

A **Lakebase** instance (Databricks' managed Postgres) named **`sunny-bay-roastery-lakebase`** is **already created**. You'll prompt **Genie Code** to wire it, attach the instance to the app, then redeploy.

#### Step 1 — Wire the checkpointer with Genie Code

Open the app's code in the workspace editor, open **Genie Code**, and paste this prompt. Type **`@`** before the skill name so Genie Code attaches the skill folder — without `@` it may not find it:

> *"Add short-term memory to this app using our Lakebase instance `sunny-bay-roastery-lakebase`,
> following the `@add-lakebase-short-term-memory` skill."*

<img src="./artifacts/Lab%203/lab_3_task_3_step_1_genie_code_skill.png" alt="Genie Code with the skill folder attached via @" width="380">

Confirm the only edit is **`start_server.py`** (the dependency and Lakebase resource are already in the repo). It should not touch the graph or the approval gate.

#### Step 2 — Attach the Lakebase instance to the app

On the app's page → **Edit → App resources → Add resource → Database instance** → pick **`sunny-bay-roastery-lakebase`** → permission **`CAN_CONNECT_AND_CREATE`** → **Save**.

<img src="./artifacts/Lab%203/lab_3_task_3_step_2_add_lakebase.png" alt="Attach the Lakebase instance as an app resource" width="680">

This grants the app's **service principal** access — the one thing the code change can't do.

> [!IMPORTANT]
> **Attach before you redeploy.** The app opens a Lakebase connection at startup. Redeploy without the resource and it **crashes** (`App crashed` on the app page).
>
> **Permission must be `CAN_CONNECT_AND_CREATE`, not `CAN_CONNECT`.** On first start the app creates the `agent_memory` schema and checkpoint tables. `CAN_CONNECT` alone fails with *`permission denied for schema public`*.

#### Step 3 — Redeploy from the UI

On the app's page click **Deploy** and wait for **Running**. If it shows **Crashed**, re-check step 2.

#### Step 4 — Prove the memory is durable

Ask **"Build my dispatch plan"**, **restart the app**, then **"approve CBM-003"** — it **still creates the order**, because Lakebase restored your plan.

> [!TIP]
> After the restart, ask **"Build my dispatch plan"** again: CBM-003 shows **✅ service order already raised** and drops off the approval list — the agent won't double-book it.

#### Step 5 — See it recorded in Lakebase

From the **product switcher** (right side of the top bar — Lakebase is its own experience, not under *Compute*), open **Database instances → `sunny-bay-roastery-lakebase`**. In **SQL Editor**, set the database to **`databricks_postgres`**, then run:

```sql
SELECT thread_id, checkpoint_id, type
FROM agent_memory.checkpoints
ORDER BY checkpoint_id DESC
LIMIT 10;
```

Those rows **are** the agent's memory — a checkpoint per step, on governed Postgres you didn't have to run.

---

> [!NOTE]
> Observing the agent with **MLflow traces** and a **Review App** is optional — see **[Observability & Feedback](./optional-deep-dives/Observability%20and%20Feedback.md)**.

---

## 💡 Key takeaways

- A custom agent **ships as a Databricks App**.
- The **control flow is in code you can read**, with a human gate before write-back.
- You can **extend it by prompting Genie Code** (here: Lakebase short-term memory).

---

## What Happens Next?

**Lab 4** uses the **AI Gateway** to publish two **governed, reusable blocks**: a **model service** (with **service policies** such as content filters) and a **you.com MCP** tool (with an **ASK** policy so a search can require approval). Later agents call those blocks instead of each team attaching their own model keys and tools.

➡️ Continue to **[Lab 4 — Govern Reusable AI Blocks](./Lab%204%20-%20Govern%20Reusable%20AI%20Blocks.md)**
