# 🔍 Lab 2 — Document Intelligence

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- Explain how Databricks turns an unstructured **PDF** into structured data with no model setup.
- Use the **Information Extraction** agent in **Agent Bricks** — Databricks' enterprise platform for building AI agents — to define a schema in plain English and extract fields, no code required.
- Turn that agent into a **Lakeflow pipeline** in one click, so new reports are extracted automatically.
- Recognise where `ai_extract()` and `ai_parse_document()` fit underneath the UI.

---

## 📖 Introduction

Marc receives fault reports as **unstructured PDF documents** — written by field
technicians after a service visit, emailed in, scanned. Before any agent can act on them,
the key facts need to be pulled out: which machine, which fault code, what happened.

Databricks does this with two built-in AI Functions — no model to train, no
embeddings, no glue code:

| Function | What it does |
|---|---|
| **`ai_parse_document()`** | Reads a PDF (or image, Word doc, slide deck) and returns its text and layout — titles, tables, paragraphs. |
| **`ai_extract()`** | Takes that text and pulls out the fields you name in plain English, returning a clean struct. |

You won't write either one by hand. **Agent Bricks** — Databricks' enterprise platform for
building AI agents, spanning low-code agents like this one through fully custom code (the
kind you'll build in Lab 3) — includes an **Information Extraction** agent that runs both
functions for you: you describe the fields you want in plain English, check the results
against the source PDFs, then turn the whole thing into a pipeline in one click. The
Lab 0 setup job already built the equivalent pipeline by hand, and you'll compare
against it at the end.

> **Marc's situation:** CBM-003 at the Mission location has thrown a pressure fault
> three times in 18 days. Sara flagged it in Lab 1. To act across all 12 locations, Marc
> needs the technicians' PDF reports as structured, queryable data — surfaced in Sara's
> Maintenance Genie now, and feeding his dispatch agent in Lab 3.

---

## Instructions

### **Step 1: Extract the fields you need — no code**

The Information Extraction agent gives you a no-code way to go straight from PDF to
structured fields. You describe what you want in plain English; it builds the schema and
runs the extraction.

**First, get a fault report onto your laptop.** The agent's setup page takes an uploaded
file, so download one of the PDFs from the volume before you start.

1. In the workspace sidebar open **Catalog** and browse to:

   ```
   <catalog> → coffee_maintenance → Volumes → fault_reports
   ```

   > [!NOTE]
   > Replace `<catalog>` with the catalog name you used in Lab 0 (e.g. `sunny_bay_roastery`).

2. Click **`FR-2026-001.pdf`** and **download** it. Open it and skim what the technician
   wrote about CBM-003 — you'll be checking the extracted fields against it shortly.

   > [!TIP]
   > Grab a second report too (say `FR-2026-004.pdf`) if you want to see the agent handle
   > more than one document.

3. In the workspace left sidebar, click **Agents**.

4. Click **Create Agent** → **Information Extraction**.

5. On the **Start with your data** page, **drag the PDF you just downloaded into the
   upload area** (or click to browse for it).

6. Click **Create Agent**.

7. Under **Configuration**, describe what you want in plain English. Start small:

   ```
   Extract the machine ID and the location.
   ```

8. Click **Generate Schema**. Agent Bricks turns that sentence into typed fields — have a
   look at what it came up with, and click **Or, Define manually** if you want to rename a
   field, change a type, or edit a description.

9. Click **Save and run extraction**.

10. The screen splits: the **source document** on the left, the **extracted JSON** on the
    right. Check the two values against the PDF you skimmed earlier.

> [!TIP]
> **Now add more fields and re-run.** Extend the description to pull out the fault code,
> the issue description, the contact, and the report date. Building it up one field at a
> time — rather than asking for everything at once — makes it obvious which description
> caused a bad extraction.
>
> Field descriptions are instructions: *"the machine ID, in the form CBM-000"* extracts far
> more reliably than *"machine"*. Iterating here in the UI is much faster than debugging
> SQL later.

---

### **Step 2: Turn it into a pipeline — one click**

You've proved the extraction works on one report. Now point it at *all* of them, so every
new field report that lands in the volume gets extracted automatically.

1. Click **Use Agent** (upper-right) and choose **Create a Lakeflow pipeline**.

2. Databricks generates a **Lakeflow Spark Declarative Pipeline** that writes the
   extracted fields into a **streaming table** and keeps it up to date on a schedule.

3. Point the pipeline's source at the full volume rather than your single uploaded file:

   ```
   /Volumes/<catalog>/coffee_maintenance/fault_reports/
   ```

4. Skim the generated code. Two things worth noticing:

   - It uses **`ai_extract()`** — the same function the UI was calling for you, now with
     the schema you designed.
   - It reads the volume incrementally, so it only processes files it hasn't seen yet.

5. Run the pipeline, then query its output table to see all 10 reports as rows.

> [!TIP]
> **`Use Agent` also offers `Run in SQL`** — that opens a SQL editor with the equivalent
> `ai_extract()` query if you'd rather explore the function by hand than build a pipeline.

> [!NOTE]
> **Two functions, two jobs.** `ai_extract()` pulls named fields out of text. Its partner
> **`ai_parse_document()`** handles the step before — turning a PDF's layout (titles,
> tables, paragraphs) into text in the first place. The Information Extraction agent runs
> both for you. If you ever need the raw parsed layout on its own, that's the
> **Document Parsing** agent type, or `ai_parse_document()` directly in SQL.

---

### **Step 3: Compare against the prebuilt pipeline**

You just built a pipeline from the UI. The Lab 0 setup job shipped one too — the same
two functions across all 10 reports, written by hand as a **Lakeflow Spark Declarative
Pipeline**. Comparing them shows you what the UI generated for you.

1. Query the prebuilt pipeline's output table:

   ```sql
   SELECT * FROM <catalog>.coffee_maintenance.fault_reports_structured
   ORDER BY report_date DESC
   ```

2. Compare a row here against the same report in your own agent's output. Same fields,
   same values — you just got there without writing the SQL.

> [!NOTE]
> **How the prebuilt pipeline works.** The same two functions, wired into a streaming
> medallion flow:
>
> ```
> New PDF dropped into Volume
>         ↓
>   fault_reports_raw        (Bronze — Auto Loader + ai_parse_document())
>         ↓
>   fault_reports_structured (Gold  — ai_extract() applied automatically)
> ```
>
> Find it in your workspace under **Jobs & Pipelines** → **Agents in a Day - Fault
> Report Pipeline**. When a new field report lands in the Volume, it is
> parsed, extracted, and appended to `fault_reports_structured` on the next run — no
> manual step.

---

### **Step 4: Add the extracted reports to the Maintenance Genie (5 min)**

In Lab 1 you built the **Sunny Bay Maintenance Genie** agent — the one Sara drives through
**Genie One** — over the structured maintenance tables. Now that the fault-report
*contents* are structured too, add them so the agent can answer about what the reports
actually say.

1. Open **Genie** → your **Sunny Bay Maintenance Genie** agent → **Settings** (data /
   tables).

2. **Add** the table you just built:

   ```
   <catalog>.coffee_maintenance.fault_reports_structured
   ```

3. Update the agent's description to mention it (so it routes report questions here):

   ```
   ...also includes fields extracted from fault report PDFs — issue descriptions,
   pressure readings, recommended parts, and technician notes.
   ```

4. Save, then ask the agent something only the reports can answer:

   ```
   What did the latest fault report for CBM-003 say, and what parts were recommended?
   ```

> [!NOTE]
> Same Genie agent Sara already uses — it just got smarter. This is also the agent
> Marc's custom agent calls in Lab 3, so wiring the reports in here means the agent
> gets them for free.

---

### **Bonus: Build Marc's dispatch plan — a preview of Lab 3 (optional, 10 min)**

You now have the fault reports as a clean table. So what would Marc actually *do* with it? He'd
rank the fleet: which machines to service this week, weighed against the revenue each store puts
at risk. That ranked shortlist is a **dispatch plan** — and it's exactly what Marc's custom
agent produces in Lab 3. Here you'll build it **once, by hand**, using a reusable **skill** —
so Lab 3's agent stops feeling like magic and starts feeling like *this logic, deployed*.

The workshop repo ships a **`dispatch-plan` skill** that encodes Marc's scoring policy — the
*same* deterministic formula the Lab 3 agent runs in code (`app/agent_server/dispatch.py`):

```
priority = 4 · unresolved_faults + revenue_at_risk_per_week / 1000
(a machine must score ≥ 10, and have an unresolved fault, to make the plan)
```

1. Open **Genie Code** (the in-product assistant) in the workspace, over the repo you cloned in
   setup — the same place you'll use it in Lab 3.

2. Type **`@`** before the skill name so Genie Code attaches the skill folder as context, then
   paste this prompt:

   > *"Build Marc's weekly dispatch plan over `<catalog>.coffee_maintenance.fault_reports_structured`,
   > following the `@dispatch-plan` skill. Show the ranked plan and the draft messages."*

3. Genie Code discovers the table shapes, applies the scoring policy, and returns a **ranked
   plan** — each machine with its location, unresolved-fault count, fault code, revenue at risk,
   priority score, and a **draft message** to that store's manager. Ask it to **show its SQL** so
   you can see the ranking is deterministic, not guessed.

> [!IMPORTANT]
> **This analysis writes nothing.** It ranks and drafts — it does not raise a service order.
> That write-back, *and the human-in-the-loop approval gate in front of it*, is what Lab 3 adds
> when it wires this same scoring into a deployed **custom agent**. You just built the agent's
> "brain" by hand; Lab 3 gives it hands (and a gate).

---

## 💡 Key takeaways

| | What you built in the UI (Steps 1–2) | The prebuilt pipeline (Step 3) |
|---|---|---|
| **Schema** | Described in plain English, generated for you | Written by hand in SQL |
| **Functions** | `ai_extract()` + `ai_parse_document()` under the hood | The same two functions, called directly |
| **Output** | A streaming table from your generated pipeline | `fault_reports_structured` Delta table |
| **Trigger** | Scheduled by the generated pipeline | Auto-triggered on new file arrival |
| **Code you wrote** | **None** | The whole pipeline |

Marc's custom agent (Lab 3) queries `fault_reports_structured` through the Maintenance
Genie. When a new field report lands in the Volume, it's extracted automatically and the
agent can act on it without any manual step.

---

## 🔀 The other option — when to just point Genie at the files

Databricks gives you a second, no-pipeline way to get insights from documents: a Genie
agent can **attach a Unity Catalog volume directly** and, at question time, retrieve and
parse the most relevant files on the fly — no extraction step, no table. See
[Genie agents over volumes](https://docs.databricks.com/aws/en/genie-agents/volumes).

So why did we extract to a table instead? It comes down to what you're asking:

| | **Attach the volume to Genie** (query-time) | **Extract to a table** (this lab) |
|---|---|---|
| **Setup** | None — just attach the volume | A pipeline + a schema |
| **Best at** | Ad-hoc "what does *this* report say?" | Precise, repeated, **aggregate** queries |
| **Across many docs** | **~5 files per question** by default | Full table: `GROUP BY`, joins, counts over *all* reports |
| **Freshness** | Always reads the live file | As fresh as the last pipeline run |
| **Cost** | Parses on every question | Parses once per file |

> [!NOTE]
> **Content search (Beta) lifts the ~5-file limit.** With it turned on, a Genie agent indexes
> the whole volume and can reason across *all* your files, not just ~5 per question. It's in
> **Beta** — if you're on a paid workspace, ask your admin to enable it and give it a try.

> [!TIP]
> **Rule of thumb:** attach the volume for exploratory Q&A over a *handful* of documents;
> extract to a table when you need reliable answers *across* the whole set. Marc's custom
> agent has to reason over every report, so the extracted table is the right foundation.

---

## What Happens Next?

Marc now has clean, structured fault data flowing out of raw PDFs. In **Lab 3** you'll
build a **custom agent** — deployed as a Databricks App — that reasons over this data
alongside sales and the web to produce Marc's dispatch plan, with a human-in-the-loop
approval gate before it acts.

➡️ Continue to **[Lab 3 — Build the Custom Agent](./Lab%203%20-%20Build%20the%20Custom%20Agent.md)**
