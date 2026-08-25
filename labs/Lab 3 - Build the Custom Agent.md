# 🤖 Lab 3 — Build & Deploy Marc's Custom Agent

> 📘 Reference: [**Author a custom agent** — Databricks docs](https://docs.databricks.com/aws/en/agents/custom-agents/author-agent)

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- **Create a custom agent app** on Databricks from the Apps UI.
- Read the agent's source code and find **where the control flow is defined**.
- Use the in-product **Genie Code assistant to add a Databricks capability** — durable **short-term
  agent memory backed by Lakebase** — without writing the code yourself.

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

That last part — *the agent takes an action, but only after a human approves* — is what
makes this a **custom agent**: it doesn't just surface an answer, it carries the workflow
through to a real write-back and waits for Marc's go-ahead before it acts.

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
replying **"approve CBM-003"**. (The in-progress plan is remembered *per signed-in user*, so
approve works as long as a plan is in progress for you — the point you'll test in Task 3.)

> [!NOTE]
> This app is built directly on the official
> [`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph)
> template — same `agent_server/` layout, same MLflow `ResponsesAgent` handlers, same built-in
> chat UI. **The only thing we changed is the agent itself:** instead of the template's generic
> tool-calling loop, it runs the explicit LangGraph pipeline above, with the approval gate. So
> what you learn here is the real template, not a bespoke fork.

---

## Instructions

### **Task 1: Create the app in the UI (10 min)**

A custom agent is just an app you deploy on Databricks. Let's stand this one up first.

1. **Get the code into your workspace** (if it isn't already): sidebar → **Workspace →
   Create → Git folder**, paste this repo's URL, **Create**. The app lives in the `app/`
   folder (that's where `app.yaml` is).

2. **Create the app**: **Compute → Apps → Create app → Custom**, name it
   `marc-dispatch-agent`, **Create**.

   <img src="./artifacts/Lab%203/lab_3_task_1_create_custom_app.png" alt="Create a custom app from the Apps UI" width="680">


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

On the app's page, click **View source** to open its code, then open
**`agent_server/dispatch.py`** — this is the agent's brain.

<img src="./artifacts/Lab%203/lab_3_task_2_view_source_code.png" alt="View source on the app page" width="680">

Two things to spot:

1. **`build_graph()`** — the four nodes and edges *are* the control flow:
   `assess → score → approval_gate ⇄ execute`. The `approval_gate` node calls
   `interrupt(...)`, which pauses the graph until your "approve" resumes it.

2. **`build_checkpointer()`** — this is the agent's **short-term memory**: where the
   in-progress plan and the pending approval are stored between your messages. Right now
   it's `MemorySaver()` — **in-memory**, so if the app restarts, the plan and pending
   approval are **gone**. That's what you'll fix in Task 3.

**Prove it forgets first (do this before Task 3):** ask **"Build my dispatch plan"**, then
**restart the app** from its page. When it's back, reply **"approve CBM-003"** — it answers
*"build a plan first"*, because in-memory state was wiped on restart. (Use a **restart**, not
a new chat — memory is keyed to you, so it survives across chats within a run; only a restart
clears `MemorySaver`.) After Task 3 wires Lakebase, you'll repeat this and it will remember.

---

### **Task 3: Add short-term memory with Lakebase — using Genie Code (10 min)**

A **Lakebase** instance (Databricks' managed Postgres) named **`sunny-bay-roastery-lakebase`** has
been **pre-created for you**. You won't write any code — you'll let **Genie Code** (the
in-product assistant) wire it in, then attach the instance to the app and redeploy.

Do these four steps **in order** — the attach (step 2) must happen **before** the redeploy
(step 3), because the app connects to Lakebase the moment it starts.

#### Step 1 — Wire the checkpointer with Genie Code

Open the app's code in the workspace editor, open **Genie Code**, and paste this short prompt.
Type **`@`** before the skill name so Genie Code attaches the skill folder as context —
without the `@` it may not find the skill:

> *"Add short-term memory to this app using our Lakebase instance `sunny-bay-roastery-lakebase`,
> following the `@add-lakebase-short-term-memory` skill."*

<img src="./artifacts/Lab%203/lab_3_task_3_step_1_genie_code_skill.png" alt="Genie Code with the skill folder attached via @" width="380">

Genie Code loads the **`add-lakebase-short-term-memory`** skill and makes the one change it
needs — wiring the Lakebase checkpointer into **`start_server.py`**. The `databricks-langchain[memory]` dependency and the
Lakebase app resource are already declared in the repo, so that's the **only file it edits**;
it doesn't touch the graph or the approval gate. Confirm the change landed only in
`start_server.py`.

#### Step 2 — Attach the Lakebase instance to the app *(do this before redeploying)*

On the app's page → **Edit → App resources → Add resource → Database instance** → pick
**`sunny-bay-roastery-lakebase`** → set the permission to **`CAN_CONNECT_AND_CREATE`** → **Save**.

<img src="./artifacts/Lab%203/lab_3_task_3_step_2_add_lakebase.png" alt="Attach the Lakebase instance as an app resource" width="680">

This grants the app's **service principal** access to the database — the one thing the code
change can't do for you.

> [!IMPORTANT]
> - **Attach before you redeploy.** The app opens a Lakebase connection at startup, so the
>   resource has to be attached first. If you redeploy without it, the app **crashes on
>   startup** (`App crashed` on the app page).
> - **The permission must be `CAN_CONNECT_AND_CREATE`, not `CAN_CONNECT`.** On first start the
>   app creates its own `agent_memory` schema and the checkpoint tables inside it. With only
>   `CAN_CONNECT` it can't create the schema and crashes with
>   *`permission denied for schema public`*.

#### Step 3 — Redeploy from the UI

On the app's page click **Deploy** to re-sync your edited code, and wait for **Running**. (If
it shows **Crashed**, re-check step 2 — the resource attach and the `CAN_CONNECT_AND_CREATE`
permission are the usual cause.)

#### Step 4 — Prove the memory is durable

Ask **"Build my dispatch plan"**, then **restart the app** from its page. When it's back,
reply **"approve CBM-003"** — it **still creates the order**, because your in-progress plan was
restored from **Lakebase** (the agent keys the memory to *you*, so it survives the restart).

> Contrast with Task 2: before Lakebase, a restart wiped the plan and the agent answered
> *"build a plan first."* That gap is what you just closed.

Want to see the memory do more than survive? After the restart, ask **"Build my dispatch
plan"** again: CBM-003 now shows **✅ service order already raised** and drops off the approval
list — the agent remembers it already acted, straight from Lakebase, and won't double-book it.

#### Step 5 — See it recorded in Lakebase

Switch to the **Lakebase** experience from the **product switcher** (the menu on the
**right side of the top bar** — Lakebase is a separate experience, not under *Compute*), then
open **Database instances → `sunny-bay-roastery-lakebase`**. In the Lakebase view, click
**SQL Editor** in the left nav, make sure the database dropdown shows
**`databricks_postgres`**, then paste this query and click **Run** (it reads the checkpoint
table the app created in the `agent_memory` schema):

```sql
SELECT thread_id, checkpoint_id, type
FROM agent_memory.checkpoints
ORDER BY checkpoint_id DESC
LIMIT 10;
```

Those rows **are** the agent's memory — a checkpoint per step of your conversation, written
straight to governed Postgres. That's your direct proof it's being recorded.

> [!NOTE]
> That's the whole point: **durable agent memory on governed Postgres you didn't have to
> run.** The pattern is short-term (thread-scoped) memory — the same one the
> [`agent-langgraph-advanced`](https://github.com/databricks/app-templates/tree/main/agent-langgraph-advanced)
> template ships.

---

> [!NOTE]
> Observing the agent with **MLflow traces** and hardening it with a **Review App** is its own
> topic — see the **[Deep Dive: Observability & Feedback](./Deep%20Dives/Observability%20and%20Feedback.md)**.

---

## 💡 Key takeaways

- **A custom agent is just an app** you create and deploy from the Databricks Apps UI.
- **The control flow lives in code you can read** — an explicit pipeline with a
  human-in-the-loop approval gate before it acts.
- **You extend the agent with Databricks capabilities, by prompting Genie Code** — you
  added durable **short-term memory on Lakebase** without writing the code yourself.

---

## What Happens Next?

Marc has a custom agent — deployed as an app, with an explicit control flow, a human-in-the-loop
approval gate, and durable memory on Lakebase. Sunny Bay's team is inspired and wants to build
more agents. In the final lab you step into the platform team's shoes and use the **AI Gateway**
to create **governed, reusable AI blocks** so every next use case inherits governance by default.

➡️ Continue to **[Lab 4 — Govern Reusable AI Blocks with the AI Gateway](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
