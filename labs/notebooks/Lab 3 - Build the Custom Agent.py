# Databricks notebook source
# MAGIC %md
# MAGIC # 🤖 Lab 3 — Build & Deploy Marc's Custom Agent
# MAGIC
# MAGIC **Persona: Marc** &nbsp;·&nbsp; **Databricks Apps · LangGraph · Lakebase · Genie Code**
# MAGIC
# MAGIC Deploy a custom agent as a Databricks App, read where its control flow lives, and add durable
# MAGIC short-term memory on Lakebase — without writing the code yourself.
# MAGIC
# MAGIC 📘 Reference: [**Author a custom agent** — Databricks docs](https://docs.databricks.com/aws/en/agents/custom-agents/author-agent)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Learning objectives
# MAGIC
# MAGIC By the end of this lab you will be able to:
# MAGIC
# MAGIC - **Create a custom agent app** on Databricks from the Apps UI.
# MAGIC - Read the agent's source code and find **where the control flow is defined**.
# MAGIC - Use the in-product **Genie Code assistant to add a Databricks capability** — durable **short-term agent memory backed by Lakebase** — without writing the code yourself.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📖 Introduction
# MAGIC
# MAGIC Sara manages one store. **Marc runs all 12.**
# MAGIC
# MAGIC Labs 1–2 gave Marc the raw signal he needs, but not the decision:
# MAGIC
# MAGIC - **Sara's Maintenance Genie (Lab 1)** — the governed, natural-language way to ask the machine/fault data *"which machines have unresolved faults, and what are the codes?"*
# MAGIC - **The field technicians' fault reports (Lab 2)** — the PDFs the techs write after a visit, turned into clean structured rows by Document Intelligence (`ai_parse_document` + `ai_extract`): which machine, which fault code, what happened.
# MAGIC
# MAGIC On his own, Marc would still have to read every field report, cross-check each store's revenue by hand,
# MAGIC and decide store-by-store who to send a technician to first — every week, across twelve locations.

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;border:1px solid #EAD9BE;border-left:4px solid #C77D2A;border-radius:12px;background:#FBF4E9;padding:16px 18px;max-width:840px">
# MAGIC   <div style="font:600 12px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#B45309;margin-bottom:4px">🤖 What Marc's custom agent is for</div>
# MAGIC   <div style="font-size:15px;line-height:1.55;color:#3a2f22">It does that legwork for him. It reads the field reports through Sara's Genie to find machines with unresolved faults, weighs each fault against the store's <b>revenue at risk</b>, and produces a <b>dispatch plan</b> — a ranked shortlist of which machines to service this week, each with a draft message to that store's manager. Marc reviews the plan and <b>approves</b> the ones worth acting on; only then does the agent raise the actual service order. <b>The manager keeps the judgement; the agent does the legwork.</b></div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC That last part — *the agent takes an action, but only after a human approves* — is what makes this a
# MAGIC **custom agent**: it doesn't just surface an answer, it carries the workflow through to a real
# MAGIC write-back and waits for Marc's go-ahead before it acts.

# COMMAND ----------

# MAGIC %md
# MAGIC ### What the dispatch plan is
# MAGIC
# MAGIC The plan is the output of an explicit **LangGraph** pipeline — control flow you can read, node by node:

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:920px">
# MAGIC   <div style="display:flex;flex-wrap:wrap;align-items:stretch;gap:10px">
# MAGIC     <div style="flex:1;min-width:150px;border:1px solid #E3D6C2;border-top:3px solid #64748B;border-radius:12px;padding:13px 15px;background:#fff">
# MAGIC       <div style="font:600 14px ui-monospace,monospace;color:#334155">assess</div>
# MAGIC       <div style="font-size:12.5px;color:#6b7280;margin-top:4px">the Genies: which machines have unresolved faults, and each store's revenue</div>
# MAGIC     </div>
# MAGIC     <div style="align-self:center;font-size:22px;color:#C77D2A;font-weight:700">→</div>
# MAGIC     <div style="flex:1;min-width:150px;border:1px solid #E3D6C2;border-top:3px solid #64748B;border-radius:12px;padding:13px 15px;background:#fff">
# MAGIC       <div style="font:600 14px ui-monospace,monospace;color:#334155">score</div>
# MAGIC       <div style="font-size:12.5px;color:#6b7280;margin-top:4px">plain Python: priority = 4·faults + revenue_at_risk/1000, then draft messages</div>
# MAGIC     </div>
# MAGIC     <div style="align-self:center;font-size:22px;color:#C77D2A;font-weight:700">→</div>
# MAGIC     <div style="flex:1;min-width:150px;border:1px solid #EAD9BE;border-top:3px solid #C77D2A;border-radius:12px;padding:13px 15px;background:#FBF4E9">
# MAGIC       <div style="font:600 14px ui-monospace,monospace;color:#B45309">approval_gate</div>
# MAGIC       <div style="font-size:12.5px;color:#8a6a3c;margin-top:4px">LangGraph <b>interrupt</b> — PAUSES here until Marc approves a machine</div>
# MAGIC     </div>
# MAGIC     <div style="align-self:center;font-size:22px;color:#2F9E68;font-weight:700">⇄</div>
# MAGIC     <div style="flex:1;min-width:150px;border:1px solid #CBEAD8;border-top:3px solid #2F9E68;border-radius:12px;padding:13px 15px;background:#F0FAF4">
# MAGIC       <div style="font:600 14px ui-monospace,monospace;color:#2F7A54">execute</div>
# MAGIC       <div style="font-size:12.5px;color:#5b7a68;margin-top:4px">create_service_order() — runs only after Marc approves</div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC In the chat, the agent returns the result as a **ranked plan**: for each machine, its location, the
# MAGIC fault count and code, the revenue at risk, the priority score, and the **draft message** to that
# MAGIC store's manager. **The plan writes nothing.** It is a recommendation until Marc approves a specific
# MAGIC machine — which he does by simply replying **"approve CBM-003"**. (The in-progress plan is remembered
# MAGIC *per signed-in user*, so approve works as long as a plan is in progress for you — the point you'll
# MAGIC test in Task 3.)
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — This app is built directly on the official
# MAGIC > [`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph) template —
# MAGIC > same `agent_server/` layout, same MLflow `ResponsesAgent` handlers, same built-in chat UI. **The only
# MAGIC > thing we changed is the agent itself:** instead of the template's generic tool-calling loop, it runs
# MAGIC > the explicit LangGraph pipeline above, with the approval gate. So what you learn here is the real
# MAGIC > template, not a bespoke fork.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 1 — Create the app in the UI
# MAGIC
# MAGIC A custom agent is just an app you deploy on Databricks. Let's stand this one up first.
# MAGIC
# MAGIC **1.** **Get the code into your workspace** (if it isn't already): sidebar → **Workspace → Create →
# MAGIC Git folder**, paste this repo's URL, **Create**. The app lives in the `app/` folder (that's where
# MAGIC `app.yaml` is).
# MAGIC
# MAGIC **2.** **Create the app**: **Compute → Apps → Create app → Custom**, name it `marc-dispatch-agent`,
# MAGIC **Create**.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%203/lab_3_task_1_create_custom_app.png" width="680" style="border-radius:8px" alt="Create a custom app from the Apps UI">

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC **3.** **Deploy it**: open the app → **Deploy** → set the source path to the `app/` folder →
# MAGIC **Deploy**, and wait for **Running**.
# MAGIC
# MAGIC The app ships in **sample-data mode**, so it deploys with **no resources to attach**. Open the app URL
# MAGIC and try it — it's a chat cockpit:

# COMMAND ----------

# MAGIC %md
# MAGIC | You say… | The agent… |
# MAGIC |---|---|
# MAGIC | **"Build my dispatch plan"** | ranks this week's machines and returns the plan |
# MAGIC | **"Why is CBM-003 ranked first?"** | explains the score from its own formula |
# MAGIC | **"Approve CBM-003"** | runs the gated `create_service_order` write-back |
# MAGIC
# MAGIC Reply **"approve CBM-003"** and the agent raises the order — but only *after* your approval.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 2 — Find where the control flow is defined
# MAGIC
# MAGIC On the app's page, click **View source** to open its code, then open **`agent_server/dispatch.py`** —
# MAGIC this is the agent's brain.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%203/lab_3_task_2_view_source_code.png" width="680" style="border-radius:8px" alt="View source on the app page">

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Two things to spot:
# MAGIC
# MAGIC **1.** **`build_graph()`** — the four nodes and edges *are* the control flow:
# MAGIC `assess → score → approval_gate ⇄ execute`. The `approval_gate` node calls `interrupt(...)`, which
# MAGIC pauses the graph until your "approve" resumes it.
# MAGIC
# MAGIC **2.** **`build_checkpointer()`** — this is the agent's **short-term memory**: where the in-progress
# MAGIC plan and the pending approval are stored between your messages. Right now it's `MemorySaver()` —
# MAGIC **in-memory**, so if the app restarts, the plan and pending approval are **gone**. That's what you'll
# MAGIC fix in Task 3.
# MAGIC
# MAGIC > ⚠️ &nbsp;**Prove it forgets first (do this before Task 3)** — ask **"Build my dispatch plan"**, then
# MAGIC > **restart the app** from its page. When it's back, reply **"approve CBM-003"** — it answers *"build a
# MAGIC > plan first"*, because in-memory state was wiped on restart. (Use a **restart**, not a new chat —
# MAGIC > memory is keyed to you, so it survives across chats within a run; only a restart clears
# MAGIC > `MemorySaver`.) After Task 3 wires Lakebase, you'll repeat this and it will remember.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 3 — Add short-term memory with Lakebase, using Genie Code
# MAGIC
# MAGIC A **Lakebase** instance (Databricks' managed Postgres) named **`sunny-bay-roastery-lakebase`** has been
# MAGIC **pre-created for you**. You won't write any code — you'll let **Genie Code** (the in-product
# MAGIC assistant) wire it in, then attach the instance to the app and redeploy.
# MAGIC
# MAGIC Do these four steps **in order** — the attach (step 2) must happen **before** the redeploy (step 3),
# MAGIC because the app connects to Lakebase the moment it starts.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 — Wire the checkpointer with Genie Code
# MAGIC
# MAGIC Open the app's code in the workspace editor, open **Genie Code**, and paste this short prompt. Type
# MAGIC **`@`** before the skill name so Genie Code attaches the skill folder as context — without the `@` it
# MAGIC may not find the skill:
# MAGIC
# MAGIC > *"Add short-term memory to this app using our Lakebase instance `sunny-bay-roastery-lakebase`,
# MAGIC > following the `@add-lakebase-short-term-memory` skill."*
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%203/lab_3_task_3_step_1_genie_code_skill.png" width="380" style="border-radius:8px" alt="Genie Code with the skill folder attached via @">

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Genie Code loads the **`add-lakebase-short-term-memory`** skill and makes the one change it needs —
# MAGIC wiring the Lakebase checkpointer into **`start_server.py`**. The `databricks-langchain[memory]`
# MAGIC dependency and the Lakebase app resource are already declared in the repo, so that's the **only file
# MAGIC it edits**; it doesn't touch the graph or the approval gate. Confirm the change landed only in
# MAGIC `start_server.py`.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 — Attach the Lakebase instance to the app *(before redeploying)*
# MAGIC
# MAGIC On the app's page → **Edit → App resources → Add resource → Database instance** → pick
# MAGIC **`sunny-bay-roastery-lakebase`** → set the permission to **`CAN_CONNECT_AND_CREATE`** → **Save**.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%203/lab_3_task_3_step_2_add_lakebase.png" width="680" style="border-radius:8px" alt="Attach the Lakebase instance as an app resource">

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC This grants the app's **service principal** access to the database — the one thing the code change
# MAGIC can't do for you.
# MAGIC
# MAGIC > ⚠️ &nbsp;**Important**
# MAGIC > - **Attach before you redeploy.** The app opens a Lakebase connection at startup, so the resource has to be attached first. If you redeploy without it, the app **crashes on startup** (`App crashed` on the app page).
# MAGIC > - **The permission must be `CAN_CONNECT_AND_CREATE`, not `CAN_CONNECT`.** On first start the app creates its own `agent_memory` schema and the checkpoint tables inside it. With only `CAN_CONNECT` it can't create the schema and crashes with *`permission denied for schema public`*.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 — Redeploy from the UI
# MAGIC
# MAGIC On the app's page click **Deploy** to re-sync your edited code, and wait for **Running**. (If it shows
# MAGIC **Crashed**, re-check step 2 — the resource attach and the `CAN_CONNECT_AND_CREATE` permission are the
# MAGIC usual cause.)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 4 — Prove the memory is durable
# MAGIC
# MAGIC Ask **"Build my dispatch plan"**, then **restart the app** from its page. When it's back, reply
# MAGIC **"approve CBM-003"** — it **still creates the order**, because your in-progress plan was restored from
# MAGIC **Lakebase** (the agent keys the memory to *you*, so it survives the restart).
# MAGIC
# MAGIC > Contrast with Task 2: before Lakebase, a restart wiped the plan and the agent answered *"build a plan
# MAGIC > first."* That gap is what you just closed.
# MAGIC
# MAGIC Want to see the memory do more than survive? After the restart, ask **"Build my dispatch plan"** again:
# MAGIC CBM-003 now shows **✅ service order already raised** and drops off the approval list — the agent
# MAGIC remembers it already acted, straight from Lakebase, and won't double-book it.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 — See it recorded in Lakebase
# MAGIC
# MAGIC Switch to the **Lakebase** experience from the **product switcher** (the menu on the **right side of
# MAGIC the top bar** — Lakebase is a separate experience, not under *Compute*), then open **Database instances
# MAGIC → `sunny-bay-roastery-lakebase`**. In the Lakebase view, click **SQL Editor** in the left nav, make
# MAGIC sure the database dropdown shows **`databricks_postgres`**, then run the query below (it reads the
# MAGIC checkpoint table the app created in the `agent_memory` schema):

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Run this in Lakebase's built-in SQL Editor (database: databricks_postgres)
# MAGIC SELECT thread_id, checkpoint_id, type
# MAGIC FROM agent_memory.checkpoints
# MAGIC ORDER BY checkpoint_id DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC Those rows **are** the agent's memory — a checkpoint per step of your conversation, written straight to
# MAGIC governed Postgres. That's your direct proof it's being recorded.
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — That's the whole point: **durable agent memory on governed Postgres you didn't have
# MAGIC > to run.** The pattern is short-term (thread-scoped) memory — the same one the
# MAGIC > [`agent-langgraph-advanced`](https://github.com/databricks/app-templates/tree/main/agent-langgraph-advanced)
# MAGIC > template ships.
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — Observing the agent with **MLflow traces** and hardening it with a **Review App** is
# MAGIC > its own topic — see the **[Deep Dive: Observability & Feedback](./Deep%20Dives/Observability%20and%20Feedback.md)**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Key takeaways
# MAGIC
# MAGIC - **A custom agent is just an app** you create and deploy from the Databricks Apps UI.
# MAGIC - **The control flow lives in code you can read** — an explicit pipeline with a human-in-the-loop approval gate before it acts.
# MAGIC - **You extend the agent with Databricks capabilities, by prompting Genie Code** — you added durable **short-term memory on Lakebase** without writing the code yourself.

# COMMAND ----------

# MAGIC %md
# MAGIC ### What happens next?
# MAGIC
# MAGIC Marc has a custom agent — deployed as an app, with an explicit control flow, a human-in-the-loop
# MAGIC approval gate, and durable memory on Lakebase. Sunny Bay's team is inspired and wants to build more
# MAGIC agents. In the final lab you step into the platform team's shoes and use the **AI Gateway** to create
# MAGIC **governed, reusable AI blocks** so every next use case inherits governance by default.
# MAGIC
# MAGIC ➡️ **Continue to [Lab 4 — Govern Reusable AI Blocks with the AI Gateway](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
