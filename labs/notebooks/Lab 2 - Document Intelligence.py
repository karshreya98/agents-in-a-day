# Databricks notebook source
# MAGIC %md
# MAGIC # 🔍 Lab 2 — Document Intelligence
# MAGIC
# MAGIC **Persona: Marc** &nbsp;·&nbsp; ~40 min &nbsp;·&nbsp; **No code required** &nbsp;·&nbsp; builds on Lab 1
# MAGIC
# MAGIC Turn a pile of unstructured **PDF fault reports** into clean, queryable data — with Databricks
# MAGIC AI functions and Agent Bricks. No model to train, no glue code, no SQL to hand-write.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Learning Objectives
# MAGIC
# MAGIC By the end of this lab you will be able to:
# MAGIC
# MAGIC - Explain how Databricks turns an unstructured **PDF** into structured data with no model setup.
# MAGIC - Use the **Information Extraction** agent in **Agent Bricks** — Databricks' enterprise platform for building AI agents — to define a schema in plain English and extract fields, no code required.
# MAGIC - Turn that agent into a **Lakeflow pipeline** in one click, so new reports are extracted automatically.
# MAGIC - Recognise where `ai_extract()` and `ai_parse_document()` fit underneath the UI.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📖 Introduction
# MAGIC
# MAGIC Marc receives fault reports as **unstructured PDF documents** — written by field
# MAGIC technicians after a service visit, emailed in, scanned. Before any agent can act on them,
# MAGIC the key facts need to be pulled out: which machine, which fault code, what happened.
# MAGIC
# MAGIC Databricks does this with two built-in AI Functions — no model to train, no
# MAGIC embeddings, no glue code:
# MAGIC
# MAGIC | Function | What it does |
# MAGIC |---|---|
# MAGIC | **`ai_parse_document()`** | Reads a PDF (or image, Word doc, slide deck) and returns its text and layout — titles, tables, paragraphs. |
# MAGIC | **`ai_extract()`** | Takes that text and pulls out the fields you name in plain English, returning a clean struct. |
# MAGIC
# MAGIC You won't write either one by hand. **Agent Bricks** — Databricks' enterprise platform for
# MAGIC building AI agents, spanning low-code agents like this one through fully custom code (the
# MAGIC kind you'll build in Lab 3) — includes an **Information Extraction** agent that runs both
# MAGIC functions for you: you describe the fields you want in plain English, check the results
# MAGIC against the source PDFs, then turn the whole thing into a pipeline in one click. The
# MAGIC Lab 0 setup job already built the equivalent pipeline by hand, and you'll compare
# MAGIC against it at the end.

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;border:1px solid #EAD9BE;border-left:4px solid #C77D2A;border-radius:12px;background:#FBF4E9;padding:16px 18px;max-width:820px">
# MAGIC   <div style="font:600 12px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#B45309;margin-bottom:4px">☕ Marc's situation</div>
# MAGIC   <div style="font-size:15px;line-height:1.55;color:#3a2f22">CBM-003 at the Mission location has thrown a pressure fault three times in 18 days. Sara flagged it in Lab 1. To act across all 12 locations, Marc needs the technicians' PDF reports as structured, queryable data — surfaced in Sara's Maintenance Genie now, and feeding his dispatch agent in Lab 3.</div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### Instructions

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1: Extract the fields you need — no code
# MAGIC
# MAGIC The Information Extraction agent gives you a no-code way to go straight from PDF to
# MAGIC structured fields. You describe what you want in plain English; it builds the schema and
# MAGIC runs the extraction.
# MAGIC
# MAGIC **First, get a fault report onto your laptop.** The agent's setup page takes an uploaded
# MAGIC file, so download one of the PDFs from the volume before you start.
# MAGIC
# MAGIC **1.** In the workspace sidebar open **Catalog** and browse to:
# MAGIC ```
# MAGIC <catalog> → coffee_maintenance → Volumes → fault_reports
# MAGIC ```
# MAGIC > 📝 &nbsp;**Note** — Replace `<catalog>` with the catalog name you used in Lab 0 (e.g. `sunny_bay_roastery`).
# MAGIC
# MAGIC **2.** Click **`FR-2026-001.pdf`** and **download** it. Open it and skim what the technician
# MAGIC wrote about CBM-003 — you'll be checking the extracted fields against it shortly.
# MAGIC > 💡 &nbsp;**Tip** — Grab a second report too (say `FR-2026-004.pdf`) if you want to see the agent handle
# MAGIC > more than one document.
# MAGIC
# MAGIC **3.** In the workspace left sidebar, click **Agents**.
# MAGIC
# MAGIC **4.** Click **Create Agent** → **Information Extraction**.
# MAGIC
# MAGIC **5.** On the **Start with your data** page, **drag the PDF you just downloaded into the
# MAGIC upload area** (or click to browse for it).
# MAGIC
# MAGIC **6.** Click **Create Agent**.
# MAGIC
# MAGIC **7.** Under **Configuration**, describe what you want in plain English. Start small:
# MAGIC ```
# MAGIC Extract the machine ID and the location.
# MAGIC ```
# MAGIC
# MAGIC **8.** Click **Generate Schema**. Agent Bricks turns that sentence into typed fields — have a
# MAGIC look at what it came up with, and click **Or, Define manually** if you want to rename a
# MAGIC field, change a type, or edit a description.
# MAGIC
# MAGIC **9.** Click **Save and run extraction**.
# MAGIC
# MAGIC **10.** The screen splits: the **source document** on the left, the **extracted JSON** on the
# MAGIC right. Check the two values against the PDF you skimmed earlier.
# MAGIC
# MAGIC > 💡 &nbsp;**Tip** — **Now add more fields and re-run.** Extend the description to pull out the fault code,
# MAGIC > the issue description, the contact, and the report date. Building it up one field at a
# MAGIC > time — rather than asking for everything at once — makes it obvious which description
# MAGIC > caused a bad extraction.
# MAGIC >
# MAGIC > Field descriptions are instructions: *"the machine ID, in the form CBM-000"* extracts far
# MAGIC > more reliably than *"machine"*. Iterating here in the UI is much faster than debugging
# MAGIC > SQL later.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2: Turn it into a pipeline — one click
# MAGIC
# MAGIC You've proved the extraction works on one report. Now point it at *all* of them, so every
# MAGIC new field report that lands in the volume gets extracted automatically.
# MAGIC
# MAGIC **1.** Click **Use Agent** (upper-right) and choose **Create a Lakeflow pipeline**.
# MAGIC
# MAGIC **2.** Databricks generates a **Lakeflow Spark Declarative Pipeline** that writes the
# MAGIC extracted fields into a **streaming table** and keeps it up to date on a schedule.
# MAGIC
# MAGIC **3.** Point the pipeline's source at the full volume rather than your single uploaded file:
# MAGIC ```
# MAGIC /Volumes/<catalog>/coffee_maintenance/fault_reports/
# MAGIC ```
# MAGIC
# MAGIC **4.** Skim the generated code. Two things worth noticing:
# MAGIC - It uses **`ai_extract()`** — the same function the UI was calling for you, now with
# MAGIC   the schema you designed.
# MAGIC - It reads the volume incrementally, so it only processes files it hasn't seen yet.
# MAGIC
# MAGIC **5.** Run the pipeline, then query its output table to see all 10 reports as rows.
# MAGIC
# MAGIC > 💡 &nbsp;**Tip** — **`Use Agent` also offers `Run in SQL`** — that opens a SQL editor with the equivalent
# MAGIC > `ai_extract()` query if you'd rather explore the function by hand than build a pipeline.
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — **Two functions, two jobs.** `ai_extract()` pulls named fields out of text. Its partner
# MAGIC > **`ai_parse_document()`** handles the step before — turning a PDF's layout (titles,
# MAGIC > tables, paragraphs) into text in the first place. The Information Extraction agent runs
# MAGIC > both for you. If you ever need the raw parsed layout on its own, that's the
# MAGIC > **Document Parsing** agent type, or `ai_parse_document()` directly in SQL.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3: Compare against the prebuilt pipeline
# MAGIC
# MAGIC You just built a pipeline from the UI. The Lab 0 setup job shipped one too — the same
# MAGIC two functions across all 10 reports, written by hand as a **Lakeflow Spark Declarative
# MAGIC Pipeline**. Comparing them shows you what the UI generated for you.
# MAGIC
# MAGIC **1.** Query the prebuilt pipeline's output table:

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM <catalog>.coffee_maintenance.fault_reports_structured
# MAGIC ORDER BY report_date DESC

# COMMAND ----------

# MAGIC %md
# MAGIC **2.** Compare a row here against the same report in your own agent's output. Same fields,
# MAGIC same values — you just got there without writing the SQL.
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — **How the prebuilt pipeline works.** The same two functions, wired into a streaming
# MAGIC > medallion flow:

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;flex-wrap:wrap;align-items:stretch;gap:10px;max-width:900px">
# MAGIC   <div style="flex:1;min-width:190px;border:1px solid #E3D6C2;border-radius:12px;padding:14px 16px;background:#fff">
# MAGIC     <div style="font:600 11px ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:#8a7256">Source</div>
# MAGIC     <div style="font:600 15px ui-monospace,monospace;margin:6px 0 3px;color:#1f2937">New PDF → Volume</div>
# MAGIC     <div style="font-size:13px;color:#6b7280">a technician drops a report</div>
# MAGIC   </div>
# MAGIC   <div style="align-self:center;font-size:24px;color:#C77D2A;font-weight:700">→</div>
# MAGIC   <div style="flex:1;min-width:190px;border:1px solid #E3D6C2;border-top:3px solid #B07A3C;border-radius:12px;padding:14px 16px;background:#fff">
# MAGIC     <div style="font:600 11px ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:#B07A3C">Bronze</div>
# MAGIC     <div style="font:600 15px ui-monospace,monospace;margin:6px 0 3px;color:#1f2937">fault_reports_raw</div>
# MAGIC     <div style="font-size:13px;color:#6b7280">Auto Loader + ai_parse_document()</div>
# MAGIC   </div>
# MAGIC   <div style="align-self:center;font-size:24px;color:#C77D2A;font-weight:700">→</div>
# MAGIC   <div style="flex:1;min-width:190px;border:1px solid #E3D6C2;border-top:3px solid #C77D2A;border-radius:12px;padding:14px 16px;background:#fff">
# MAGIC     <div style="font:600 11px ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:#C77D2A">Gold</div>
# MAGIC     <div style="font:600 15px ui-monospace,monospace;margin:6px 0 3px;color:#1f2937">fault_reports_structured</div>
# MAGIC     <div style="font-size:13px;color:#6b7280">ai_extract() applied automatically</div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 &nbsp;Find it in your workspace under **Jobs & Pipelines** → **Agents in a Day - Fault
# MAGIC > Report Pipeline**. When a new field report lands in the Volume, it is
# MAGIC > parsed, extracted, and appended to `fault_reports_structured` on the next run — no
# MAGIC > manual step.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 4: Add the extracted reports to the Maintenance Genie (5 min)
# MAGIC
# MAGIC In Lab 1 you built the **Sunny Bay Maintenance Genie** agent — the one Sara drives through
# MAGIC **Genie One** — over the structured maintenance tables. Now that the fault-report
# MAGIC *contents* are structured too, add them so the agent can answer about what the reports
# MAGIC actually say.
# MAGIC
# MAGIC **1.** Open **Genie** → your **Sunny Bay Maintenance Genie** agent → **Settings** (data /
# MAGIC tables).
# MAGIC
# MAGIC **2.** **Add** the table you just built:
# MAGIC ```
# MAGIC <catalog>.coffee_maintenance.fault_reports_structured
# MAGIC ```
# MAGIC
# MAGIC **3.** Update the agent's description to mention it (so it routes report questions here):
# MAGIC ```
# MAGIC ...also includes fields extracted from fault report PDFs — issue descriptions,
# MAGIC pressure readings, recommended parts, and technician notes.
# MAGIC ```
# MAGIC
# MAGIC **4.** Save, then ask the agent something only the reports can answer:
# MAGIC ```
# MAGIC What did the latest fault report for CBM-003 say, and what parts were recommended?
# MAGIC ```
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — Same Genie agent Sara already uses — it just got smarter. This is also the agent
# MAGIC > Marc's custom agent calls in Lab 3, so wiring the reports in here means the agent
# MAGIC > gets them for free.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Bonus: Build Marc's dispatch plan — a preview of Lab 3 (optional, 10 min)
# MAGIC
# MAGIC You now have the fault reports as a clean table. So what would Marc actually *do* with it? He'd
# MAGIC rank the fleet: which machines to service this week, weighed against the revenue each store puts
# MAGIC at risk. That ranked shortlist is a **dispatch plan** — and it's exactly what Marc's custom
# MAGIC agent produces in Lab 3. Here you'll build it **once, by hand**, using a reusable **skill** —
# MAGIC so Lab 3's agent stops feeling like magic and starts feeling like *this logic, deployed*.
# MAGIC
# MAGIC The workshop repo ships a **`dispatch-plan` skill** that encodes a scoring policy in the same
# MAGIC spirit as Marc's Lab 3 agent — unresolved faults weighed against the revenue at risk (Lab 3
# MAGIC tunes its own numbers in `app/agent_server/dispatch.py`):

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;text-align:center;border:1px solid #D9C9B0;border-radius:12px;background:#FAF4EA;padding:18px 20px;max-width:760px">
# MAGIC   <div style="font:600 clamp(15px,2.6vw,19px) ui-monospace,monospace;color:#1f2937">priority = <span style="color:#B45309">5</span> · unresolved_faults + revenue_at_risk_per_week / <span style="color:#B45309">100</span></div>
# MAGIC   <div style="font:500 13px ui-monospace,monospace;color:#6b7280;margin-top:8px">always dispatch a machine with 2+ unresolved faults; for a single fault, dispatch where the store has real revenue at risk (score ≥ 6)</div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC **1.** Open **Genie Code** (the in-product assistant) in the workspace, over the repo you cloned in
# MAGIC setup — the same place you'll use it in Lab 3.
# MAGIC
# MAGIC **2.** Type **`@`** before the skill name so Genie Code attaches the skill folder as context, then
# MAGIC paste this prompt:
# MAGIC > *"Build Marc's weekly dispatch plan over `<catalog>.coffee_maintenance.fault_reports_structured`,
# MAGIC > following the `@dispatch-plan` skill. Show the ranked plan and the draft messages."*
# MAGIC
# MAGIC **3.** Genie Code discovers the table shapes, applies the scoring policy, and returns a **ranked
# MAGIC plan** — each machine with its location, unresolved-fault count, fault code, revenue at risk,
# MAGIC priority score, and a **draft message** to that store's manager. Ask it to **show its SQL** so
# MAGIC you can see the ranking is deterministic, not guessed.
# MAGIC
# MAGIC > ⚠️ &nbsp;**Important** — **This analysis writes nothing.** It ranks and drafts — it does not raise a service order.
# MAGIC > That write-back, *and the human-in-the-loop approval gate in front of it*, is what Lab 3 adds
# MAGIC > when it wires this same scoring into a deployed **custom agent**. You just built the agent's
# MAGIC > "brain" by hand; Lab 3 gives it hands (and a gate).

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Key takeaways
# MAGIC
# MAGIC | | What you built in the UI (Steps 1–2) | The prebuilt pipeline (Step 3) |
# MAGIC |---|---|---|
# MAGIC | **Schema** | Described in plain English, generated for you | Written by hand in SQL |
# MAGIC | **Functions** | `ai_extract()` + `ai_parse_document()` under the hood | The same two functions, called directly |
# MAGIC | **Output** | A streaming table from your generated pipeline | `fault_reports_structured` Delta table |
# MAGIC | **Trigger** | Scheduled by the generated pipeline | Auto-triggered on new file arrival |
# MAGIC | **Code you wrote** | **None** | The whole pipeline |
# MAGIC
# MAGIC Marc's custom agent (Lab 3) queries `fault_reports_structured` through the Maintenance
# MAGIC Genie. When a new field report lands in the Volume, it's extracted automatically and the
# MAGIC agent can act on it without any manual step.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🔀 The other option — when to just point Genie at the files
# MAGIC
# MAGIC Databricks gives you a second, no-pipeline way to get insights from documents: a Genie
# MAGIC agent can **attach a Unity Catalog volume directly** and, at question time, retrieve and
# MAGIC parse the most relevant files on the fly — no extraction step, no table. See
# MAGIC [Genie agents over volumes](https://docs.databricks.com/aws/en/genie-agents/volumes).
# MAGIC
# MAGIC So why did we extract to a table instead? It comes down to what you're asking:

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:900px">
# MAGIC   <div style="text-align:center;margin:2px 0 18px">
# MAGIC     <div style="font:700 24px system-ui;color:#1f2937">Two ways to ask your documents</div>
# MAGIC     <div style="font:600 16px system-ui;color:#B45309;margin-top:2px">When to point Genie at files vs. extract to a table</div>
# MAGIC   </div>
# MAGIC   <div style="display:flex;flex-wrap:wrap;gap:16px">
# MAGIC     <div style="flex:1;min-width:290px;border:1px solid #E5E7EB;border-top:4px solid #64748B;border-radius:14px;padding:18px;background:#fff">
# MAGIC       <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
# MAGIC         <div style="width:40px;height:40px;border-radius:10px;background:#F1F5F9;display:flex;align-items:center;justify-content:center;font-size:20px">📁</div>
# MAGIC         <div><div style="font:700 18px system-ui;color:#334155">Attach the volume to Genie</div><div style="font-size:13px;color:#64748b">query-time · no pipeline</div></div>
# MAGIC       </div>
# MAGIC       <div style="display:flex;gap:10px;background:#F8FAFC;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Zero setup</div><div style="font-size:13px;color:#5b6470">Just attach the volume — no pipeline, no schema.</div></div></div>
# MAGIC       <div style="display:flex;gap:10px;background:#F8FAFC;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Great for ad-hoc lookups</div><div style="font-size:13px;color:#5b6470">"What does <i>this</i> report say?"</div></div></div>
# MAGIC       <div style="display:flex;gap:10px;background:#FBF4E9;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#C77D2A;font-weight:800">!</span><div><div style="font:600 14px system-ui;color:#1f2937">~5 files per question by default</div><div style="font-size:13px;color:#5b6470">Content search (Beta) lifts this — see below.</div></div></div>
# MAGIC     </div>
# MAGIC     <div style="flex:1;min-width:290px;border:1px solid #CBEAD8;border-top:4px solid #2F9E68;border-radius:14px;padding:18px;background:#fff;position:relative">
# MAGIC       <div style="position:absolute;top:14px;right:14px;font:600 10px ui-monospace,monospace;letter-spacing:.08em;color:#2F7A54;background:#E4F5EC;border:1px solid #BFE6D0;border-radius:99px;padding:3px 9px">THIS LAB</div>
# MAGIC       <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
# MAGIC         <div style="width:40px;height:40px;border-radius:10px;background:#E9F6EF;display:flex;align-items:center;justify-content:center;font-size:20px">🗄️</div>
# MAGIC         <div><div style="font:700 18px system-ui;color:#2F7A54">Extract to a table</div><div style="font-size:13px;color:#5f8b74">reliable · repeatable</div></div>
# MAGIC       </div>
# MAGIC       <div style="display:flex;gap:10px;background:#F0FAF4;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Aggregate queries</div><div style="font-size:13px;color:#5b6470"><code>GROUP BY</code>, joins, counts over <i>all</i> reports.</div></div></div>
# MAGIC       <div style="display:flex;gap:10px;background:#F0FAF4;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Reliable across the whole set</div><div style="font-size:13px;color:#5b6470">No per-question file cap.</div></div></div>
# MAGIC       <div style="display:flex;gap:10px;background:#F0FAF4;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div><div style="font:600 14px system-ui;color:#1f2937">Parses once per file</div><div style="font-size:13px;color:#5b6470">As fresh as the last pipeline run.</div></div></div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 &nbsp;**Note** — **Content search (Beta) lifts the ~5-file limit.** With it turned on, a Genie agent indexes
# MAGIC > the whole volume and can reason across *all* your files, not just ~5 per question. It's in
# MAGIC > **Beta** — if you're on a paid workspace, ask your admin to enable it and give it a try.
# MAGIC
# MAGIC > 💡 &nbsp;**Tip** — **Rule of thumb:** attach the volume for exploratory Q&A over a *handful* of documents;
# MAGIC > extract to a table when you need reliable answers *across* the whole set. Marc's custom
# MAGIC > agent has to reason over every report, so the extracted table is the right foundation.

# COMMAND ----------

# MAGIC %md
# MAGIC ### What Happens Next?
# MAGIC
# MAGIC Marc now has clean, structured fault data flowing out of raw PDFs. In **Lab 3** you'll
# MAGIC build a **custom agent** — deployed as a Databricks App — that reasons over this data
# MAGIC alongside sales and the web to produce Marc's dispatch plan, with a human-in-the-loop
# MAGIC approval gate before it acts.
# MAGIC
# MAGIC ➡️ Continue to Lab 3 — Build the Custom Agent
