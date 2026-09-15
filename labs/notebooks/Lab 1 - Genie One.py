# Databricks notebook source
# MAGIC %md
# MAGIC # 🗣️ Lab 1 — Genie One
# MAGIC
# MAGIC **Persona: Sara** &nbsp;·&nbsp; **No code required** &nbsp;·&nbsp; Genie One + Genie agents
# MAGIC
# MAGIC Sara just wants answers. Build a governed **Genie agent** over the maintenance data, drive it from
# MAGIC **Genie One**, enrich it with live web knowledge, then package her weekly check as a scheduled **skill**.
# MAGIC
# MAGIC 📘 Reference: [**Genie One** — Databricks docs](https://docs.databricks.com/aws/en/genie-one/)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Learning Objectives
# MAGIC
# MAGIC By the end of Lab 1, you will be able to:
# MAGIC
# MAGIC - Build a **Genie agent** (formerly *Genie space*) over the Sunny Bay maintenance data.
# MAGIC - Use **Genie One** as a business-user interface, driven by that Genie agent.
# MAGIC - Connect an external **MCP tool** (you.com) to enrich Genie One conversations with live web knowledge.
# MAGIC - Package a repeated question as a reusable **skill** and put it on a **schedule**, so Genie One briefs Sara automatically.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Key concepts
# MAGIC
# MAGIC | Term | What it means here |
# MAGIC |---|---|
# MAGIC | **Genie agent** | A governed natural-language interface over specific Unity Catalog tables (menus may still say *Genie space* — same thing). You build the Maintenance one; Sales is pre-built. |
# MAGIC | **Genie One** | The chat front door. It **routes** each question to the Genie agent whose description matches — you don't pick a space first. |
# MAGIC | **MCP** | *Model Context Protocol* — a standard way to plug an external tool (here, you.com web search) into Genie One or the AI Gateway. |
# MAGIC | **Skill** | A saved prompt/capability in Genie One so Sara doesn't re-type the same question. You can **schedule** a skill to run on a cadence. |

# COMMAND ----------

# DBTITLE 1,Cell 4
# MAGIC %md
# MAGIC ### Introduction
# MAGIC
# MAGIC Sara is the Mission location manager at Sunny Bay Roastery. Day to day she doesn't
# MAGIC write SQL or dig through tables — she just wants answers. She gets them through
# MAGIC **Genie One**, the conversational front door to Databricks. Behind Genie One sits a
# MAGIC **Genie agent**: a governed, natural-language interface to a set of Unity Catalog tables.
# MAGIC
# MAGIC > 📝 &nbsp;**Naming:** Genie agents were previously called **Genie spaces** — you'll still see
# MAGIC > "space" in some menus and URLs. They're the same thing; this lab uses **Genie agent**.
# MAGIC
# MAGIC In this lab you'll wear two hats: first you set up the Genie agent (a quick,
# MAGIC one-time build), then you step into Sara's shoes and just ask questions.
# MAGIC
# MAGIC You build **one** Genie agent here — a **Maintenance Genie** (the one Sara, and later
# MAGIC Marc's custom agent in Lab 3, needs for machine faults) — over the maintenance tables the
# MAGIC Lab 0 seeded. Lab 0 also **pre-built a Sales Genie** (Sunny Bay coffee sales
# MAGIC by store), so you end up with two agents in the workspace and talk to *both* through
# MAGIC Genie One, which routes each question to the right agent.
# MAGIC
# MAGIC This lab is **facilitator-led with participant follow-along**. No code to write. Just one
# MAGIC Genie agent and a few conversations.

# COMMAND ----------

# DBTITLE 1,Cell 5
# MAGIC %md
# MAGIC ### Step 1: Build the Maintenance Genie agent
# MAGIC
# MAGIC Lab 0 already created the core maintenance tables. Now you'll put a Genie
# MAGIC agent in front of them.
# MAGIC
# MAGIC **1.** In the workspace left sidebar, click **Genie**.
# MAGIC
# MAGIC **2.** Click **New** (or **+ New Genie Agent**).
# MAGIC
# MAGIC **3.** When prompted for data, add these three tables from the shared `sunny_bay_roastery` catalog's `coffee_maintenance` schema:
# MAGIC ```
# MAGIC sunny_bay_roastery.coffee_maintenance.machines
# MAGIC sunny_bay_roastery.coffee_maintenance.fault_events
# MAGIC sunny_bay_roastery.coffee_maintenance.service_orders
# MAGIC ```
# MAGIC > 📝 &nbsp;Use the shared `sunny_bay_roastery` catalog for all labs. If you need to create
# MAGIC > your own objects, create a dedicated schema in this catalog (e.g.
# MAGIC > `sunny_bay_roastery.<your_name>`).
# MAGIC
# MAGIC **4.** Name the Genie Agent **`Sunny Bay Maintenance Genie - <your name>`** (e.g.
# MAGIC `Sunny Bay Maintenance Genie - Sara`) so each participant has their own, and give it a description:
# MAGIC ```
# MAGIC Natural-language Q&A over Sunny Bay espresso machine maintenance: machine registry, fault event history, and service orders. Use for questions about a machine's faults, fault codes, locations, and service history. Covers machines CBM-001 to CBM-012, fault codes such as E-07 pressure faults, the 12 Sunny Bay locations including Mission District, and open or completed service orders.
# MAGIC ```
# MAGIC > ⚠️ &nbsp;**Important** — **Be generous and specific in this description.** Genie One uses it to decide
# MAGIC > whether *this* agent is the right one to answer a question. Name the actual
# MAGIC > entities a user might mention — machine IDs, fault codes, location names,
# MAGIC > the words "service order" — so questions phrased in the user's own language
# MAGIC > still match. A thin description is the most common reason Genie One skips an
# MAGIC > agent (see the callout in Step 3).
# MAGIC
# MAGIC > 💡 &nbsp;You'll reuse this exact Genie agent in **Lab 3** as one of the tools Marc's custom
# MAGIC > agent composes — building it once here means it's ready when you get there.
# MAGIC
# MAGIC > 📝 &nbsp;**You already have a second agent — Lab 0 pre-built a `Sunny Bay Sales Genie`**
# MAGIC > over the governed sales **metric view** (`sunny_bay_roastery.gold.sm_fact_coffee_sales_genie`),
# MAGIC > exposing measures like gross revenue, profit, and units sold sliced by store, product,
# MAGIC > and date. You don't build it — you'll just talk to it through Genie One in Step 3.
# MAGIC
# MAGIC > 📝 &nbsp;You now have two Genie agents in the workspace — the maintenance one you just built and
# MAGIC > the pre-built sales one. That's exactly what Genie One needs to demonstrate routing in
# MAGIC > Step 3, and both become tools of Marc's custom agent in Lab 3.

# COMMAND ----------

# DBTITLE 1,Cell 6
# MAGIC %md
# MAGIC ### Step 2: Ask maintenance questions in the Genie agent
# MAGIC
# MAGIC **1.** In the Genie agent you just built, make sure you're in **chat mode** (use the mode
# MAGIC selector in the conversation box — it may default to agent mode). Then start a conversation
# MAGIC and try:
# MAGIC ```
# MAGIC Which machines have logged E-07 pressure faults?
# MAGIC ```
# MAGIC ```
# MAGIC Show me the fault event history for the Mission District location
# MAGIC ```
# MAGIC ```
# MAGIC Which machines are due for service?
# MAGIC ```
# MAGIC
# MAGIC **2.** In chat mode, click **Show code** beneath any
# MAGIC answer to see the SQL Genie generated — no one wrote it by hand. *(Agent mode doesn't
# MAGIC expose the SQL this way.)*
# MAGIC
# MAGIC **A Genie agent has two modes — chat and agent.** Look for the mode selector in the
# MAGIC conversation box and try the same question in each.

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;flex-wrap:wrap;gap:16px;max-width:900px">
# MAGIC   <div style="flex:1;min-width:280px;border:1px solid #E5E7EB;border-top:4px solid #64748B;border-radius:14px;padding:18px;background:#fff">
# MAGIC     <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
# MAGIC       <div style="width:40px;height:40px;border-radius:10px;background:#F1F5F9;display:flex;align-items:center;justify-content:center;font-size:20px">💬</div>
# MAGIC       <div><div style="font:700 18px system-ui;color:#334155">Chat mode</div><div style="font-size:13px;color:#64748b">one question → one query → one answer</div></div>
# MAGIC     </div>
# MAGIC     <div style="display:flex;gap:10px;background:#F8FAFC;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Quick, direct lookups</div><div style="font-size:13px;color:#5b6470">"Which machines logged E-07 faults?"</div></div></div>
# MAGIC     <div style="display:flex;gap:10px;background:#F8FAFC;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Faster</div><div style="font-size:13px;color:#5b6470">Verified answers when your admin blessed the query.</div></div></div>
# MAGIC   </div>
# MAGIC   <div style="flex:1;min-width:280px;border:1px solid #E3D6C2;border-top:4px solid #C77D2A;border-radius:14px;padding:18px;background:#fff">
# MAGIC     <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
# MAGIC       <div style="width:40px;height:40px;border-radius:10px;background:#FBF4E9;display:flex;align-items:center;justify-content:center;font-size:20px">🧠</div>
# MAGIC       <div><div style="font:700 18px system-ui;color:#B45309">Agent mode</div><div style="font-size:13px;color:#a07b4e">plans, then chains several queries</div></div>
# MAGIC     </div>
# MAGIC     <div style="display:flex;gap:10px;background:#FBF7EF;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#C77D2A;font-weight:800">✦</span><div><div style="font:600 14px system-ui;color:#1f2937">Broader, multi-part questions</div><div style="font-size:13px;color:#5b6470">"Which machines need attention this week and why?"</div></div></div>
# MAGIC     <div style="display:flex;gap:10px;background:#FBF7EF;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#C77D2A;font-weight:800">✦</span><div><div style="font:600 14px system-ui;color:#1f2937">Reasons more freely</div><div style="font-size:13px;color:#5b6470">Slower, since it does more work.</div></div></div>
# MAGIC   </div>
# MAGIC </div>
# MAGIC <div style="font-family:system-ui;font-size:13px;color:#6b7280;margin-top:10px;max-width:900px">Same governed tables and same Unity Catalog permissions either way — the difference is how much reasoning Genie does before it answers.</div>

# COMMAND ----------

# MAGIC %md
# MAGIC > 💡 &nbsp;Ask *"which machines need attention this week and why?"* in **chat mode**, then again in
# MAGIC > **agent mode**. Chat mode gives you one query's worth of answer; agent mode breaks the
# MAGIC > question down and works through it. That contrast is exactly what you're building at
# MAGIC > scale in Lab 3 — the custom agent runs this kind of planning across *multiple* tools.
# MAGIC
# MAGIC > 📝 &nbsp;Genie answers from the governed tables only — right now, the machine registry, fault
# MAGIC > events, and service orders. It can't yet read the *fault report PDFs*; that's what
# MAGIC > Lab 2 adds.

# COMMAND ----------

# DBTITLE 1,Cell 9
# MAGIC %md
# MAGIC ### Step 3: Talk to your Genie agents through Genie One
# MAGIC
# MAGIC Genie One is the business-user front door. Every Genie agent in the workspace shows
# MAGIC up here as an **agent** — including the **Sunny Bay Maintenance Genie** you just built
# MAGIC *and* the pre-built **Sunny Bay Sales Genie**. Sara doesn't pick a table or an agent; she
# MAGIC just asks, and Genie One routes to the right one.
# MAGIC
# MAGIC **1.** Open the **grid menu** (the **⋮⋮⋮** icon in the top navigation bar — three columns of dots) and
# MAGIC select **Genie One**.
# MAGIC
# MAGIC <img src="../artifacts/Lab%201/one.png" width="620" style="border-radius:8px" alt="Grid menu in the top navigation bar with Genie One highlighted">
# MAGIC
# MAGIC You'll land on the Genie One page:
# MAGIC
# MAGIC <img src="../artifacts/Lab%201/one_page.png" width="620" style="border-radius:8px" alt="The Genie One page — a single chat interface that routes to your Genie agents">
# MAGIC
# MAGIC **2.** Ask Sara's manager questions — a mix of **maintenance** and **sales**. Genie One
# MAGIC routes each to the right Genie agent:
# MAGIC
# MAGIC **Maintenance** (routes to the Sunny Bay Maintenance Genie you built):
# MAGIC ```
# MAGIC Which of my machines should I be worried about this week?
# MAGIC ```
# MAGIC ```
# MAGIC How many unresolved faults does CBM-003 have?
# MAGIC ```
# MAGIC **Sales** (routes to the pre-built Sunny Bay Sales Genie):
# MAGIC ```
# MAGIC How do sales at the Sunny Bay – Mission store compare to the other stores?
# MAGIC ```
# MAGIC ```
# MAGIC Which store had the highest coffee revenue in 2024?
# MAGIC ```
# MAGIC
# MAGIC **3.** **Check *what* answered you.** Click the **citation icons** in a response to see the
# MAGIC knowledge sources Genie One used. You want to see your **Genie agent** named there —
# MAGIC not just a bare SQL result.
# MAGIC
# MAGIC > 📝 &nbsp;One conversation, two governed Genie agents — maintenance *and* sales — with no
# MAGIC > switching. Sara configured nothing; she just asks. Unity Catalog governs what each
# MAGIC > agent can see.
# MAGIC
# MAGIC **If the answer came back as a direct query instead of via your Genie agent.**
# MAGIC This is expected behaviour, not a bug. Genie One resolves a question in this order:

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;flex-wrap:wrap;align-items:stretch;gap:10px;max-width:900px">
# MAGIC   <div style="flex:1;min-width:210px;border:1px solid #E5E7EB;border-top:3px solid #2C6BAB;border-radius:12px;padding:14px 16px;background:#fff">
# MAGIC     <div style="font:700 13px ui-monospace,monospace;color:#2C6BAB">1 · SEARCH</div>
# MAGIC     <div style="font-size:14px;color:#1f2937;margin-top:5px">Searches the available <b>Genie agents</b> for one relevant to your question.</div>
# MAGIC   </div>
# MAGIC   <div style="align-self:center;font-size:22px;color:#94a3b8;font-weight:700">→</div>
# MAGIC   <div style="flex:1;min-width:210px;border:1px solid #CBEAD8;border-top:3px solid #2F9E68;border-radius:12px;padding:14px 16px;background:#fff">
# MAGIC     <div style="font:700 13px ui-monospace,monospace;color:#2F7A54">2 · MATCH</div>
# MAGIC     <div style="font-size:14px;color:#1f2937;margin-top:5px">If it finds a match, it uses <b>that agent</b> to answer. ✓</div>
# MAGIC   </div>
# MAGIC   <div style="align-self:center;font-size:22px;color:#94a3b8;font-weight:700">→</div>
# MAGIC   <div style="flex:1;min-width:210px;border:1px solid #EAD9BE;border-top:3px solid #C77D2A;border-radius:12px;padding:14px 16px;background:#fff">
# MAGIC     <div style="font:700 13px ui-monospace,monospace;color:#B45309">3 · FALL BACK</div>
# MAGIC     <div style="font-size:14px;color:#1f2937;margin-top:5px">No match → searches <b>data assets</b> directly (a raw query result, no agent named).</div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC > ⚠️ &nbsp;**Important** — So an answer with no agent attribution means step 1 didn't match. Fixes, in order of
# MAGIC > effectiveness:
# MAGIC >
# MAGIC > - **Enrich the agent description** (Step 1, task 4). This is the single biggest lever —
# MAGIC >   it's the text Genie One matches against. Add the machine IDs, fault codes, and
# MAGIC >   location names a user would actually say.
# MAGIC > - **Use vocabulary that only that agent covers.** "How many unresolved *faults* does
# MAGIC >   *CBM-003* have?" matches far more reliably than "how are my machines doing?".
# MAGIC > - **Ask it explicitly:** *"Using the Sunny Bay Maintenance Genie, which machines have
# MAGIC >   logged E-07 faults?"*
# MAGIC > - **Or pick the agent by hand.** If Genie One's chat doesn't route well, click **Ask** in
# MAGIC >   the search bar and select the Genie agent yourself — that bypasses routing entirely and
# MAGIC >   drops you straight into the agent (where you also get the chat/agent mode selector from
# MAGIC >   Step 2).
# MAGIC >
# MAGIC > **Facilitator tip:** this is worth demoing deliberately. Ask a vague question, show the
# MAGIC > unattributed query result, then improve the description and ask again. Watching the
# MAGIC > agent *become* the source teaches why descriptions are routing rules — the same lesson
# MAGIC > Lab 3 builds on when the custom agent picks between its tools.

# COMMAND ----------

# DBTITLE 1,Cell 12
# MAGIC %md
# MAGIC ### Step 4: Connect you.com for live web knowledge
# MAGIC
# MAGIC The telemetry tells Sara *what* is happening. It cannot tell her *why*, or what the
# MAGIC manufacturer recommends. An external **MCP service** (you.com), registered in the Unity
# MAGIC Unity Gateway, fixes that.
# MAGIC
# MAGIC > 📝 &nbsp;**Built-in web search (Beta).** Databricks now also offers a built-in web search in
# MAGIC > **Genie Code** that works without any MCP setup — see
# MAGIC > [Search the web](https://docs.databricks.com/aws/en/genie-code/web-search). We use the
# MAGIC > **you.com MCP service** here because it registers a **governed, reusable AI block** in the
# MAGIC > Unity Gateway — the pattern Lab 4 builds on — and makes the web tool available to Genie One
# MAGIC > and any future agent.
# MAGIC
# MAGIC **Step 4a — Confirm the you.com MCP service exists**
# MAGIC
# MAGIC The setup job should have already registered the **`you_web_search_mcp`** MCP service
# MAGIC (backed by the **`youcom_http_secondary`** connection). Confirm it's there:
# MAGIC
# MAGIC Sidebar → **Unity Gateway → MCPs** → look for **`you_web_search_mcp`**.
# MAGIC
# MAGIC - **Found it** → skip straight to **Step 4c**.
# MAGIC - **Not there** → follow **Step 4b** below to create it.

# COMMAND ----------

# DBTITLE 1,Cell 13
# MAGIC %md
# MAGIC **Step 4b — *(For reference)* How the you.com MCP service was created**
# MAGIC
# MAGIC > You do **not** need to create anything here — the setup job already registered
# MAGIC > `you_web_search_mcp` and its underlying `youcom_http_secondary` connection. This section
# MAGIC > explains how it was done, in case you ever need to recreate it on your own workspace.
# MAGIC
# MAGIC The MCP service was created via **Unity Gateway → MCPs → Create MCP Service** with an
# MAGIC HTTP connection pointing at `https://api.you.com:443/mcp` (Bearer token auth, you.com API
# MAGIC key).
# MAGIC
# MAGIC > ⚠️ &nbsp;**Key detail — metastore-level connection.** The underlying HTTP connection
# MAGIC > (`youcom_http_secondary`) must be created at the **metastore level**, not inside a
# MAGIC > catalog/schema. MCP services require a metastore-level connection to be visible across
# MAGIC > the workspace. If you ever recreate this, choose **Metastore** as the connection scope
# MAGIC > during creation.
# MAGIC
# MAGIC **Step 4c — Ask enriched questions**
# MAGIC
# MAGIC In Genie One, enable the you.com MCP service: **Customizations → Connectors** → toggle **`you_web_search_mcp`** on.
# MAGIC
# MAGIC > ⚠️ &nbsp;**On your own workspace** — connectors in Genie One are a **Beta**. If you don't see the
# MAGIC > **Customizations > Connectors** tab, a **workspace admin** must enable **"Third Party Connectors
# MAGIC > for Agents"** on the **Previews** page first. See
# MAGIC > [Connect to external tools and sources](https://docs.databricks.com/aws/en/genie-one/external-sources).
# MAGIC
# MAGIC <img src="../artifacts/Lab%201/lab_1_step_4c_enable_youcom_in_genie_one.png" width="620" style="border-radius:8px" alt="Genie One → Customizations → Connections with the you.com MCP connection toggled on">
# MAGIC
# MAGIC You can now ask questions that combine your governed data with the web:
# MAGIC ```
# MAGIC What does the manufacturer recommend when a repeated E-07 pressure error
# MAGIC appears on a commercial espresso machine?
# MAGIC ```
# MAGIC ```
# MAGIC Are there any known service bulletins for pressure faults on commercial
# MAGIC espresso machines?
# MAGIC ```
# MAGIC
# MAGIC > 📝 &nbsp;Internal maintenance data and live web knowledge in the same conversation. Unity
# MAGIC > Catalog data never moved — the context just got richer.

# COMMAND ----------

# DBTITLE 1,Cell 14
# MAGIC %md
# MAGIC ### Step 5: Turn Sara's weekly check into a skill — and schedule it (optional)
# MAGIC
# MAGIC Sara keeps asking the same weekly question: *which machines need attention, and why?*
# MAGIC Genie One lets her stop re-typing it. Two features turn a repeated question into something
# MAGIC durable:
# MAGIC
# MAGIC - A **skill** — a custom, reusable capability she creates once and runs any time.
# MAGIC - A **scheduled task** — a question (or skill) Genie One re-runs on a cadence and emails to
# MAGIC   her as a briefing, no prompting required.
# MAGIC
# MAGIC Additionally, Sara wants to send the results of her findings to her maintenance team. Genie One supports managed connections
# MAGIC with GSuite and MS365. For this Lab, we will use Gmail.
# MAGIC
# MAGIC > ⚠️ &nbsp;**Important** — **Enable the connector: click the `+` below the text box and toggle on Gmail.**
# MAGIC > Use the shared workshop Gmail account below, or your own personal Gmail. The agent will
# MAGIC > only create a draft — it won't send anything.
# MAGIC >
# MAGIC > | | |
# MAGIC > |---|---|
# MAGIC > | **Email** | `sunnybayroastery@gmail.com` |
# MAGIC > | **Password** | `sunnybayroastery_dbx` |
# MAGIC
# MAGIC > 📝 &nbsp;**Skills and scheduled tasks are personal to you.** A skill you create lives in your own
# MAGIC > Genie One — it isn't shared with the workspace. In the near future, skills will be shareable
# MAGIC > enabling teams to share standard and best practices.
# MAGIC
# MAGIC **Step 5a — Create a skill**
# MAGIC
# MAGIC In Genie One chat, just describe the capability you want. Genie One writes the skill and
# MAGIC saves it for you:
# MAGIC ```
# MAGIC Create a user skill called "maintenance update email drafter".
# MAGIC
# MAGIC When the skill is invoked or if you are asked to prepare a maintenance update:
# MAGIC
# MAGIC 1. Use the Sunny Bay Maintenance Genie to identify relevant machines, recent faults and
# MAGIC    repeated fault codes.
# MAGIC
# MAGIC 2. Using the Gmail connector, draft an email to maintenance@sunnybailroastery.com:
# MAGIC    - Start with a clear subject line.
# MAGIC    - Summarize the situation in plain business language.
# MAGIC    - Identify affected machines and locations.
# MAGIC    - Explain the operational impact without unnecessary technical jargon.
# MAGIC    - List recommended actions, owners, and urgency.
# MAGIC    - End with a clear request or next step.
# MAGIC ```
# MAGIC
# MAGIC Genie One creates the skill and saves it to your workspace at
# MAGIC `/Workspace/Users/<your-email>/.assistant/skills/` and accessible on the tab `Customizations > Skill`
# MAGIC where it can be edited or deleted and (soon) shared.
# MAGIC
# MAGIC **Step 5b — Execute the skill**
# MAGIC
# MAGIC Two ways to run it:
# MAGIC
# MAGIC - **Invoke it by hand:** type `/` in the chat input and pick your skill from the list.
# MAGIC - **Let Genie One load it:** just ask a related question. Genie One automatically loads the
# MAGIC   skill when it decides the skill is relevant to your request — you don't have to name it.
# MAGIC
# MAGIC You still get **Show code** and the **citation icons** on the answer, exactly as in Steps 2–3.
# MAGIC
# MAGIC At the end of the skill execution, a new draft will be written in Gmail.
# MAGIC
# MAGIC **Step 5c — Schedule it as a standing briefing**
# MAGIC
# MAGIC Now make it run itself. The fastest way is to just ask in chat:
# MAGIC ```
# MAGIC Run maintenance update email drafter every Monday at 7am.
# MAGIC ```
# MAGIC
# MAGIC Or create it deliberately from the sidebar:
# MAGIC
# MAGIC **1.** In the Genie One sidebar, click **Schedules**.
# MAGIC
# MAGIC **2.** Open the dropdown next to **+ Create in chat** and choose **Create manually**.
# MAGIC
# MAGIC **3.** Fill in **Title**, **Instructions** (the question or skill to run), **Connections** (the
# MAGIC data/agent the task should use — your Maintenance Genie agent, plus you.com for bulletins),
# MAGIC **Schedule** (e.g. weekly, Monday 07:00), and **Timezone**.
# MAGIC
# MAGIC **4.** Click **Create**. Use **Run now** to fire it immediately and check the output.
# MAGIC
# MAGIC When the task runs it **posts the results in a chat thread and emails you the results with a
# MAGIC PDF attachment** — so Sara gets her Monday briefing whether or not she's in Databricks that
# MAGIC morning.
# MAGIC
# MAGIC > 📝 &nbsp;Manage every scheduled task under **Scheduled tasks** in the sidebar: click one to see its
# MAGIC > past runs, edit it, or delete it. To pull a task into a fresh conversation, **@mention** it
# MAGIC > in chat.
# MAGIC
# MAGIC > 📝 &nbsp;**Facilitator note:** Skills and scheduled tasks are newer Genie One capabilities. Confirm
# MAGIC > they're enabled in your workshop workspace before the session — some Free Edition workspaces
# MAGIC > may not have them yet. If they're unavailable, demonstrate the *intent* instead: Sara defines
# MAGIC > the weekly machine-health question once, and Genie One runs it for her every Monday morning.
# MAGIC
# MAGIC The point stands either way: **Sara defines the *question* once. Genie does the *work* — on
# MAGIC demand and on a schedule.**
# MAGIC
# MAGIC Full reference: [Chat in Genie One](https://docs.databricks.com/aws/en/genie-one/chat)
# MAGIC (covers both user skills and scheduled tasks).

# COMMAND ----------

# DBTITLE 1,Cell 15
# MAGIC %md
# MAGIC ### Bridge to Marc's Arc
# MAGIC
# MAGIC Sara's machine check just flagged **CBM-003: pressure anomaly, repeated E-07 fault
# MAGIC codes**.
# MAGIC
# MAGIC She can *see* it. But who decides what to *do* about it — across all 12 locations at once?
# MAGIC
# MAGIC That's **Marc**, the operations manager. He runs the 12 location managers (Sara among
# MAGIC them) and has to prioritise: which machines threaten which stores, who to dispatch, and
# MAGIC who to tell. The fault history is already in Unity Catalog — the same Maintenance Genie
# MAGIC Sara queried knows it. The question is whether Marc has something that turns it into a
# MAGIC *decision and an action*.
# MAGIC
# MAGIC **Over Labs 2–3 you build that — Lab 2 adds document intelligence, Lab 3 builds
# MAGIC and deploys the custom agent. Lab 4 governs the AI building blocks underneath.**

# COMMAND ----------

# MAGIC %md
# MAGIC ### What Happens Next?
# MAGIC
# MAGIC You have built a Genie agent, driven it from Genie One as a business user, enriched it with
# MAGIC live web knowledge — and, optionally, packaged Sara's weekly check as a scheduled skill that
# MAGIC briefs her automatically — all on governed data that never left Unity Catalog.
# MAGIC
# MAGIC ➡️ Continue to Lab 2 — Document Intelligence