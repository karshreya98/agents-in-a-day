# Agents in a Day 🤖

A hands-on 4-hour workshop that adds an **action layer** to your Databricks
workspace — built on top of **Dashboard in a Day**.

---

## ⚠️ Prerequisite — Complete Dashboard in a Day first

Agents in a Day builds on the Unity Catalog, metric view, and Genie Agent
created by DAID. **You must complete DAID before running this setup.**

### DAID install checklist

1. Clone the DAID repo as a Git Folder in your workspace:
   ```
   https://github.com/DatabricksDashboardInADay/DatabricksDashboardInADay
   ```
2. Open `bundle/databricks.yml` → set `catalog` to your catalog name
3. Click **Deploy** in the bundle editor toolbar
4. Go to **Workflows** → find **"Sunny Bay Roastery Setup"** → click **Run now**
5. Wait for the green **Succeeded** badge (~5 min)

Once DAID is done, come back here and follow the steps below.

---

## Getting started

### Step 1 — Clone this repo as a Git Folder

1. In your Databricks workspace go to **Workspace** (left sidebar)
2. Click **+ Add** → **Git Folder**
3. Paste: `https://github.com/karshreya98/agents-in-a-day`
4. Click **Create Git Folder**

---

### Step 2 — Set your catalog name in `databricks.yml`

1. Open `bundle/databricks.yml` in the workspace
2. Change the `catalog` default to match what you used in DAID:

```yaml
variables:
  catalog:
    default: sunny_bay_roastery   # ← change this to your catalog
```

> **Not sure?** Open `labs/Lab 0 - Setup`, run the catalog picker cell to see
> which catalogs you have access to.

---

### Step 3 — Deploy the bundle

1. With `bundle/databricks.yml` open, click **Deploy** (top-right toolbar)
2. You should see a green **"Bundle deployed successfully"** message

---

### Step 4 — Run the setup job

1. Go to **Workflows** in the left sidebar
2. Find **"Agents in a Day — Setup"** and click **Run now**
3. Wait for the green **Succeeded** badge (~5 min)

The job creates:
- `coffee_maintenance` schema with `machines`, `fault_events`, `service_orders` tables
- 5 fault report PDFs in a UC Volume
- `fault_reports_structured` table — the Lakeflow pipeline runs `ai_parse_document()`
  + `ai_extract()` across all 5 PDFs (used in Lab 1)
- `create_service_order` UC function

---

## Workshop Labs

| Lab | Character | What you build |
|-----|-----------|----------------|
| **Part 1** | Sara | Genie One + you.com MCP — briefings without touching data |
| **Lab 1** | Marc | Document Intelligence — `ai_parse_document()` + `ai_extract()` on fault report PDFs |
| **Lab 2** | Marc | Build the Supervisor — Agent Bricks multi-source agent |
| **Lab 3** | Marc | Share, Test, and Harden — test scenarios + guardrails |
| **Lab 4** | Marc | AI Gateway + write-back — `create_service_order` UC function |

All labs are in the `labs/` folder.

---

## Repo structure

```
agents-in-a-day/
├── bundle/
│   ├── databricks.yml          ← Set your catalog here, then Deploy
│   ├── resources/
│   │   ├── job.yml             ← Setup job (runs the notebook + pipeline)
│   │   └── pipeline.yml        ← Lakeflow pipeline (parses + extracts all PDFs)
│   └── src/
│       ├── data/fault_reports/ ← 5 prebuilt fault report PDFs
│       ├── notebooks/
│       │   └── Lab 0 - Setup.py        ← Setup notebook (run via the job above)
│       └── transformations/
│           └── fault_report_pipeline.py ← ai_parse_document + ai_extract
├── labs/
│   ├── Part 1 - Sara - Genie One.md
│   ├── Lab 1 - Document Intelligence.md
│   ├── Lab 2 - Build the Supervisor.md
│   ├── Lab 3 - Share and Test.md
│   └── Lab 4 - AI Gateway and Write-back.md
└── README.md
```
