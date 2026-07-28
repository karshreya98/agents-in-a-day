# Agents in a Day 🤖

A hands-on 4-hour workshop that adds an **action layer** to your Databricks
workspace — built on top of **Dashboard in a Day**.

---

## Setup — Install Dashboard in a Day (for its data & artifacts)

Agents in a Day builds on the Unity Catalog, metric view, and Sales Genie created by
Dashboard in a Day (DAID). You don't need to *run the DAID workshop* — just install it
so its data and artifacts exist in your workspace.

### Install DAID

1. Clone the DAID repo as a Git Folder in your workspace:
   ```
   https://github.com/DatabricksDashboardInADay/DatabricksDashboardInADay
   ```
2. Open `bundle/databricks.yml` → set `catalog` to your catalog name
3. Click **Deploy** in the bundle editor toolbar
4. Go to **Workflows** → find **"Sunny Bay Roastery Setup"** → click **Run now**
5. Wait for the green **Succeeded** badge (~5 min)

That's it — the DAID data and Sales Genie are now in your workspace. Continue below.

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
2. Change the `catalog` default to match the catalog you installed DAID into:

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
  + `ai_extract()` across all 5 PDFs (used in Lab 2)
- `create_service_order` UC function

---

## Workshop Labs

| Lab | Character | What you build |
|-----|-----------|----------------|
| **Lab 1** | Sara | Build a Genie space, drive it from Genie One, enrich with you.com MCP |
| **Lab 2** | Marc | Document Intelligence — `ai_parse_document()` + `ai_extract()` on fault report PDFs |
| **Lab 3** | Marc | Build the Supervisor — Agent Bricks multi-source agent |
| **Lab 4** | Marc | Observe and Review — MLflow traces + Review App for expert feedback |
| **Lab 5** | Platform | Governed AI coding — Unity AI Gateway + PII guardrail + `ucode` vibe-codes the write-back |

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
│   ├── Lab 1 - Sara - Genie One.md
│   ├── Lab 2 - Document Intelligence.md
│   ├── Lab 3 - Build the Supervisor.md
│   ├── Lab 4 - Observe and Review.md
│   └── Lab 5 - AI Gateway and Write-back.md
│   (artifacts/ holds per-lab screenshots)
└── README.md
```
