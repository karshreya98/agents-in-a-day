# 🔍 Lab 2 — Document Intelligence

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- Explain how Databricks turns an unstructured **PDF** into structured data with no model setup.
- Use the **Document Parsing** agent in Agent Bricks to parse a fault report in the UI.
- Run `ai_parse_document()` and `ai_extract()` yourself in a notebook on **one** fault report.
- Understand how the same two functions run automatically across **all** fault reports in a Lakeflow pipeline.

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

You will meet both — first in the **Agent Bricks UI**, then in a **notebook** — on a
single fault report. The Lab 0 setup job has already run them across all 5 reports
into a Delta table, and you'll compare your result against it at the end.

> **Marc's situation:** CBM-003 at the Mission location has thrown a pressure fault
> three times in 18 days. Sara flagged it in Lab 1. Marc needs to read the fault
> report and understand what the technician wrote — before he can create a service order.

---

## Instructions

### **Step 1: Parse a fault report in Agent Bricks**

Agent Bricks gives you a no-code way to try document parsing before you write a
single line of SQL.

1. In the workspace left sidebar, click **Agents**.

2. Click **Create Agent** → **Document Parsing**.

3. Under **source document**, choose **Select from a volume** and browse to:

   ```
   /Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.pdf
   ```

   > [!NOTE]
   > Replace `<catalog>` with the catalog name you used in Lab 0 (e.g. `sunny_bay_roastery`).

4. Click **Parse document** and wait a few moments.

5. The screen splits: the **source PDF** on the left, the **parsed output** on the
   right. Toggle between **formatted text** and **raw JSON** to see how Databricks
   broke the document into elements (title, table, paragraphs) with confidence scores.

> [!TIP]
> This is exactly what `ai_parse_document()` returns — the UI is just a friendly
> front end over the same function. In the next step you'll run it yourself.

6. When you're done exploring, click **Use Agent** → **Run in Notebook**. This opens
   a notebook pre-filled with an `ai_parse_document()` query pointed at the volume.

---

### **Step 2: Extract structured fields in a notebook**

Now you'll go from *parsed text* to *structured columns* — the shape an agent can
actually query.

1. In the notebook that just opened (or a **New** → **Notebook** set to **Serverless**
   and **SQL**), you'll build up the query in three cells.

2. **Parse the PDF into text.** In the first cell, paste and run:

   ```sql
   WITH parsed AS (
     SELECT ai_parse_document(content) AS doc
     FROM READ_FILES(
       '/Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.pdf',
       format => 'binaryFile'
     )
   )
   SELECT
     array_join(
       transform(
         try_cast(doc:document:elements AS ARRAY<STRING>),
         x -> from_json(x, 'STRUCT<content: STRING>').content
       ),
       '\n'
     ) AS raw_text
   FROM parsed
   ```

   You'll see the text Sara wrote about CBM-003, stitched together from the parsed
   elements — the same content the UI showed you in Step 1.

3. **Extract the fields you care about.** In a new cell, wrap that text in
   `ai_extract()` and name the fields in plain English:

   ```sql
   WITH parsed AS (
     SELECT ai_parse_document(content) AS doc
     FROM READ_FILES(
       '/Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.pdf',
       format => 'binaryFile'
     )
   ),
   raw AS (
     SELECT array_join(
       transform(
         try_cast(doc:document:elements AS ARRAY<STRING>),
         x -> from_json(x, 'STRUCT<content: STRING>').content
       ),
       '\n'
     ) AS raw_text
     FROM parsed
   )
   SELECT
     ai_extract(
       raw_text,
       array(
         'machine_id', 'machine_model', 'fault_code',
         'issue_description', 'location_name',
         'contact_name', 'report_date'
       )
     ) AS fields
   FROM raw
   ```

   `ai_extract()` returns a **struct** with one field per name you gave it.

4. **Flatten the struct into columns.** In a new cell, pull each field out with dot
   notation:

   ```sql
   WITH parsed AS (
     SELECT ai_parse_document(content) AS doc
     FROM READ_FILES(
       '/Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.pdf',
       format => 'binaryFile'
     )
   ),
   raw AS (
     SELECT array_join(
       transform(
         try_cast(doc:document:elements AS ARRAY<STRING>),
         x -> from_json(x, 'STRUCT<content: STRING>').content
       ),
       '\n'
     ) AS raw_text
     FROM parsed
   ),
   extracted AS (
     SELECT ai_extract(
       raw_text,
       array(
         'machine_id', 'machine_model', 'fault_code',
         'issue_description', 'location_name',
         'contact_name', 'report_date'
       )
     ) AS fields
     FROM raw
   )
   SELECT
     fields.machine_id        AS machine_id,
     fields.machine_model     AS machine_model,
     fields.fault_code        AS fault_code,
     fields.issue_description AS issue_description,
     fields.location_name     AS location_name,
     fields.contact_name      AS contact_name,
     fields.report_date       AS report_date
   FROM extracted
   ```

   You should get one clean row: `CBM-003`, `Siemens EQ.9 Plus Connect`, `E-07`, and the rest.

> [!TIP]
> `ai_extract()` returns a struct, so you read fields with dot notation
> (`fields.machine_id`) — no `json_extract()` needed.

---

### **Step 3: See it run at scale — the Lakeflow pipeline**

You just did this for **one** PDF. The Lab 0 setup job already ran the *exact same
two functions* across **all 5** fault reports using a **Lakeflow Spark Declarative
Pipeline**, and saved the result to a Delta table.

1. Query the pipeline's output table:

   ```sql
   SELECT * FROM <catalog>.coffee_maintenance.fault_reports_structured
   ORDER BY report_date DESC
   ```

2. Find the row for `FR-2026-001.pdf` — it matches the single row you produced in
   Step 2 exactly. The pipeline did the same work, for every report, automatically.

> [!NOTE]
> **How the pipeline works.** It's the same two functions you just ran, wired into a
> streaming medallion flow:
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
> notebook needed.

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

| | What you did (Steps 1–2) | What the pipeline does (Step 3) |
|---|---|---|
| **Input** | 1 fault report PDF | Every PDF dropped into the Volume |
| **Functions** | `ai_parse_document()` + `ai_extract()` | The same two functions |
| **Output** | 1 structured row | `fault_reports_structured` Delta table, always up to date |
| **Trigger** | You ran a cell | Auto-triggered on new file arrival |

Marc's Supervisor (Lab 3) queries `fault_reports_structured` as one of its tools. When
Sara drops a new PDF into the Volume, it's extracted automatically and the Supervisor
can act on it without any manual step.

---

## What Happens Next?

Marc now has clean, structured fault data flowing out of raw PDFs. In **Lab 3** you'll
build the **Supervisor Agent** that queries this table — alongside machine telemetry
and the web — to give Marc a single field-ready briefing.

➡️ Continue to **[Lab 3 — Build the Supervisor](./Lab%203%20-%20Build%20the%20Supervisor.md)**
