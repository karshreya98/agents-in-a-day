# 🔍 Lab 1 — Document Intelligence

## 🎯 Goal

Marc receives fault reports as **unstructured text files** — written by location managers, emailed in, scanned. Before any agent can act on them, the key facts need to be pulled out: which machine, which fault code, what happened.

In this lab you will use **`ai_extract()`** — a built-in Databricks AI Function — to turn one raw fault report into clean, structured data in a single SQL call. No model setup. No embeddings. No glue code. You describe the fields you want in plain English; Databricks handles the rest.

> **Marc's situation:** CBM-003 at the Mission location has thrown a pressure fault three times in 18 days. Sara flagged it in Part 1. Marc needs to read the fault report and understand what the technician wrote — before he can create a service order.

---

## 🧪 Try it — extract one fault report

### Step 1 — Open a new notebook

1. In the left sidebar click **New** → **Notebook**
2. Set the compute to **Serverless**
3. Set the language to **SQL**

---

### Step 2 — Read the raw fault report

In the first cell, paste and run:

```sql
SELECT read_files(
  '/Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.txt',
  format => 'text'
) AS raw_text
```

> Replace `<catalog>` with the catalog name you used in Lab 0 (e.g. `sunny_bay_roastery`).

You will see the raw text Sara wrote about CBM-003 — unstructured, exactly as she typed it.

---

### Step 3 — Extract structured fields with `ai_extract()`

In a new cell, run:

```sql
WITH raw AS (
  SELECT read_files(
    '/Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.txt',
    format => 'text'
  ) AS raw_text
)
SELECT
  ai_extract(
    raw_text,
    array(
      'machine_id',
      'machine_model',
      'fault_code',
      'issue_description',
      'location_name',
      'contact_name',
      'report_date'
    )
  ) AS extracted
FROM raw
```

You will see a JSON object with every field pulled out automatically.

> **What just happened?** You described the fields you wanted in plain English. `ai_extract()` called the Foundation Model API and mapped them from the free text — no training, no fine-tuning.

---

### Step 4 — Flatten the JSON into columns

In a new cell, run:

```sql
WITH raw AS (
  SELECT read_files(
    '/Volumes/<catalog>/coffee_maintenance/fault_reports/FR-2026-001.txt',
    format => 'text'
  ) AS raw_text
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
  fields:machine_id        AS machine_id,
  fields:machine_model     AS machine_model,
  fields:fault_code        AS fault_code,
  fields:issue_description AS issue_description,
  fields:location_name     AS location_name,
  fields:contact_name      AS contact_name,
  fields:report_date       AS report_date
FROM extracted
```

> **Tip:** The `:` syntax (`fields:machine_id`) is Spark's inline JSON path accessor — no `json_extract()` needed.

---

### Step 5 — Compare with the full pipeline output

The Lab 0 setup job already ran `ai_extract()` across **all 5 fault reports** and saved the results. Query it now:

```sql
SELECT * FROM <catalog>.coffee_maintenance.fault_reports_structured
ORDER BY report_date DESC
```

Your single-file extraction from Step 4 matches row 1 exactly. The pipeline did the same thing — at scale, automatically.

---

## 💡 Key takeaways

| | What you did | What the pipeline does |
|---|---|---|
| **Input** | 1 fault report file | Every file dropped into the Volume |
| **Function** | `ai_extract()` | Same `ai_extract()` |
| **Output** | 1 structured row | `fault_reports_structured` Delta table, always up to date |
| **Trigger** | You ran a cell | Auto-triggered on new file arrival |

Marc's Supervisor (Lab 2) queries `fault_reports_structured` as one of its tools. When Sara drops a new PDF into the Volume, it is extracted automatically and the Supervisor can act on it without any manual step.

---

## ⚙️ How this runs at scale — the SDP pipeline

> **Facilitator note / for the curious**

The Lab 0 setup job deployed a **Spark Declarative Pipeline** (`fault_report_pipeline.py`) that automates everything you just did manually:

```
New .txt file dropped into Volume
        ↓
  fault_reports_raw        (Bronze — Auto Loader streaming table)
        ↓
  fault_reports_structured (Gold  — ai_extract() applied automatically)
```

You can find it in your workspace under **Delta Live Tables** (search for `Agents in a Day`). In a production scenario you would trigger this pipeline on a schedule or on file arrival — no notebook needed.

---

➡️ Continue to **[Lab 2 — Build the Supervisor](./Lab%202%20-%20Build%20the%20Supervisor.md)**
