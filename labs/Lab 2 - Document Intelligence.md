# 🔍 Lab 2 — Document Intelligence

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- Explain how Databricks turns an unstructured **PDF** into structured data with no model setup.
- Use the **Information Extraction** agent in Agent Bricks to define a schema in plain English and extract fields — no code.
- Turn that agent into a **Lakeflow pipeline** in one click, so new reports are extracted automatically.
- Recognise where `ai_extract()` and `ai_parse_document()` fit underneath the UI.

---

## 📖 Introduction

Marc receives fault reports as **unstructured PDF documents** — written by location
managers, emailed in, scanned. Before any agent can act on them, the key facts need
to be pulled out: which machine, which fault code, what happened.

Databricks does this with two built-in AI Functions — no model to train, no
embeddings, no glue code:

| Function | What it does |
|---|---|
| **`ai_parse_document()`** | Reads a PDF (or image, Word doc, slide deck) and returns its text and layout — titles, tables, paragraphs. |
| **`ai_extract()`** | Takes that text and pulls out the fields you name in plain English, returning a clean struct. |

You won't write either one by hand. The **Information Extraction** agent in Agent Bricks
runs both for you: you describe the fields you want in plain English, check the results
against the source PDFs, then turn the whole thing into a pipeline in one click. The
Lab 0 setup job already built the equivalent pipeline by hand, and you'll compare
against it at the end.

> **Marc's situation:** CBM-003 at the Mission location has thrown a pressure fault
> three times in 18 days. Sara flagged it in Lab 1. Marc needs to read the fault
> report and understand what the technician wrote — before he can create a service order.

---

## Instructions

### **Step 1: Extract the fields you need — no code**

Agent Bricks gives you a no-code way to go straight from PDF to structured fields. You
describe what you want in plain English; it builds the schema and runs the extraction.

**First, get a fault report onto your laptop.** The agent's setup page takes an uploaded
file, so download one of the PDFs from the volume before you start.

1. In the workspace sidebar open **Catalog** and browse to:

   ```
   <catalog> → coffee_maintenance → Volumes → fault_reports
   ```

   > [!NOTE]
   > Replace `<catalog>` with the catalog name you used in Lab 0 (e.g. `sunny_bay_roastery`).

2. Click **`FR-2026-001.pdf`** and **download** it. Open it and skim what Sara wrote about
   CBM-003 — you'll be checking the extracted fields against it shortly.

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
PDF Sara drops in the volume gets extracted automatically.

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
> Report Pipeline**. When Sara drops a new fault report PDF into the Volume, it is
> parsed, extracted, and appended to `fault_reports_structured` on the next run — no
> manual step.

---

### **Step 4: Add the extracted reports to the Maintenance Genie (5 min)**

In Lab 1 you built the **Sunny Bay Maintenance Genie** over the structured maintenance
tables. Now that the fault-report *contents* are structured too, add them so the agent
can answer about what the reports actually say.

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
> Marc's Supervisor calls in Lab 3, so wiring the reports in here means the Supervisor
> gets them for free.

---

## 💡 Key takeaways

| | What you built in the UI (Steps 1–2) | The prebuilt pipeline (Step 3) |
|---|---|---|
| **Schema** | Described in plain English, generated for you | Written by hand in SQL |
| **Functions** | `ai_extract()` + `ai_parse_document()` under the hood | The same two functions, called directly |
| **Output** | A streaming table from your generated pipeline | `fault_reports_structured` Delta table |
| **Trigger** | Scheduled by the generated pipeline | Auto-triggered on new file arrival |
| **Code you wrote** | **None** | The whole pipeline |

Marc's Supervisor (Lab 3) queries `fault_reports_structured` as one of its tools. When
Sara drops a new PDF into the Volume, it's extracted automatically and the Supervisor
can act on it without any manual step.

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
| **Across many docs** | Limited — only **~5 files read per question** | Full table: `GROUP BY`, joins, counts over *all* reports |
| **Freshness** | Always reads the live file | As fresh as the last pipeline run |
| **Cost** | Parses on every question | Parses once per file |

> [!IMPORTANT]
> **We have 10 fault reports — and Genie only reads ~5 files per question.** So if you
> just attached the volume and asked *"across all our reports, which machines have
> recurring pressure faults?"*, Genie would answer from at most half the documents and
> quietly miss the rest. The extracted table has no such limit — it queries all 10 rows
> at once.

> [!TIP]
> **Rule of thumb:** attach the volume for exploratory Q&A over a *handful* of documents;
> extract to a table when you need reliable answers *across* the whole set. Marc's
> Supervisor has to reason over every report ("which machines need attention this
> week?"), so the extracted table is the right foundation. (You could still attach the
> volume too, for a deep dive into a single report.)

---

## What Happens Next?

Marc now has clean, structured fault data flowing out of raw PDFs. In **Lab 3** you'll
build the **Supervisor Agent** that queries this table — alongside machine telemetry
and the web — to give Marc a single field-ready briefing.

➡️ Continue to **[Lab 3 — Build the Supervisor](./Lab%203%20-%20Build%20the%20Supervisor.md)**
