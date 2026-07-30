# Agents in a Day 🤖

A hands-on 4-hour workshop that adds an **action layer** to your Databricks
workspace — built on top of **Dashboard in a Day**.

Two personas at a fictional coffee-machine operator, **Sunny Bay Roastery**:
**Sara** (a location manager who just wants answers) and **Marc** (a field technician
who needs to act). Across five labs you turn governed data + unstructured PDFs into
Genie agents, a multi-source Supervisor agent, human-feedback review, and governed
AI-assisted coding — all on Databricks, no infrastructure to provision.

## What you'll build

| Lab | Persona | What you build |
|-----|---------|----------------|
| **Lab 1** | Sara | A Genie agent over maintenance data, driven from Genie One, enriched with a you.com MCP tool |
| **Lab 2** | Marc | Document intelligence — `ai_parse_document()` + `ai_extract()` turn fault-report PDFs into a table |
| **Lab 3** | Marc | A **Supervisor Agent** (Agent Bricks) that reasons across Genie + web |
| **Lab 4** | Marc | Observe it with MLflow traces; collect expert feedback via a Review App |
| **Lab 5** | Platform | Governed AI-assisted coding — Unity AI Gateway + PII guardrail + `ucode`/OpenCode |

## Prerequisites

- A Databricks workspace with **Unity Catalog** and **serverless compute** enabled, and a
  running serverless **SQL warehouse**.
- A region that supports **AI Functions** (`ai_parse_document`, `ai_extract`), **Agent
  Bricks**, and — for Lab 5 — the **Unity AI Gateway (Beta)**.
- **Dashboard in a Day** installed in the same catalog (see below) — it provides the
  sales data and Sales Genie the labs build on.
- **Lab 5 only:** an account admin must enable the **Unity AI Gateway (Beta)** and
  **Managed MCP Servers** previews (account console → Previews). Participants install
  [`ucode`](https://github.com/databricks/ucode) + [OpenCode](https://opencode.ai) locally.

> Running this for a group? See each lab's admin/prerequisite callouts — one admin sets up
> the shared catalog, registers the you.com MCP service, governs a model for Lab 5, and
> grants participants access.

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
- 10 fault report PDFs in a UC Volume
- `fault_reports_structured` table — the Lakeflow pipeline runs `ai_parse_document()`
  + `ai_extract()` across all 10 PDFs (used in Lab 2)
- `create_service_order` UC function

---

## Workshop Labs

All labs are step-by-step markdown in the **`labs/`** folder — start with
**Lab 1** and follow the ➡️ links at the bottom of each. (See the *What you'll build*
table above for the arc.)

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
│       ├── data/fault_reports/ ← 10 prebuilt fault report PDFs
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
