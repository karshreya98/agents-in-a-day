# Agents in a Day 🤖

A hands-on 4-hour workshop that adds an **action layer** to your Databricks
workspace.

Two personas at a fictional coffee-machine operator, **Sunny Bay Roastery**:
**Sara** (a location manager who just wants answers) and **Marc** (a field technician
who needs to act). Across five labs you turn governed data + unstructured PDFs into
Genie agents, a multi-source Supervisor agent, human-feedback review, and governed
AI-assisted coding — all on Databricks, no infrastructure to provision.

## What you'll build

| Lab | Persona | What you build |
|-----|---------|----------------|
| **Lab 1** | Sara | Two Genie agents (maintenance + sales) driven from Genie One, enriched with a you.com MCP tool |
| **Lab 2** | Marc | Document intelligence — `ai_parse_document()` + `ai_extract()` turn fault-report PDFs into a table |
| **Lab 3** | Marc | A **Supervisor Agent** (Agent Bricks) that reasons across Genie + web |
| **Lab 4** | Marc | Observe it with MLflow traces; collect expert feedback via a Review App |
| **Lab 5** | Platform | Governed AI-assisted coding — Unity AI Gateway + PII guardrail + `ucode`/OpenCode |

## Prerequisites

- A Databricks workspace with **Unity Catalog** and **serverless compute** enabled, and a
  running serverless **SQL warehouse**. The bundle looks this warehouse up by name —
  it defaults to **"Serverless Starter Warehouse"** (present on Free Edition). On a shared
  workspace with a different name, update the `warehouse_id` lookup in `bundle/databricks.yml`.
- A region that supports **AI Functions** (`ai_parse_document`, `ai_extract`), **Agent
  Bricks**, and — for Lab 5 — the **Unity AI Gateway (Beta)**.
- A Unity Catalog **catalog you can write to**. On Free Edition, create a new one (e.g.
  `sunny_bay_roastery`). The setup step seeds all the data — no other workshop to install.
- **Lab 5 only:** an account admin must enable the **Unity AI Gateway (Beta)** and
  **Managed MCP Servers** previews (account console → Previews). Participants install
  [`ucode`](https://github.com/databricks/ucode) + [OpenCode](https://opencode.ai) locally.

> Running this for a group? See each lab's admin/prerequisite callouts — one admin
> registers the you.com MCP service, governs a model for Lab 5, and grants participants
> access. Give each participant their own catalog so their tables don't collide.

---

## Getting started

The setup job builds everything the labs need — maintenance data, the full Sunny Bay
sales star schema + metric view (vendored from Dashboard in a Day), a pre-built Sales
Genie and sales dashboard, the fault-report PDFs, and the `fault_reports_structured`
table (via a Lakeflow pipeline).

### Step 1 — Clone this repo as a Git Folder

1. In your Databricks workspace go to **Workspace** (left sidebar)
2. Click **+ Add** → **Git Folder**
3. Paste: `https://github.com/karshreya98/agents-in-a-day`
4. Click **Create Git Folder**

---

### Step 2 — Deploy the bundle and run the setup job

1. Open `bundle/databricks.yml` and set the `catalog` default to the catalog you want to
   use:

   ```yaml
   variables:
     catalog:
       default: sunny_bay_roastery   # ← change this to your catalog
   ```

   > **Not sure which catalog you can write to?** Open `bundle/src/notebooks/Lab 0 - Setup`
   > and run its **first cell** — it lists every catalog you have access to.

2. Click **Deploy** (top-right toolbar). You should see **"Bundle deployed successfully"**.

3. Go to **Workflows** in the left sidebar, find **"Agents in a Day - Setup"**, and click
   **Run now**. Wait for the green **Succeeded** badge (~5 min).

The job creates:
- `coffee_maintenance` schema with `machines`, `fault_events`, `service_orders` tables
- `gold` sales star schema — `fact_coffee_sales` + `dim_store`/`dim_product`/`dim_customer`/`dim_date`
  (generated + transformed by the sales pipeline, history from 2010)
- `gold.sm_fact_coffee_sales_genie` — a governed **metric view** over the star schema
- **Sunny Bay Sales Genie** — pre-built over the metric view (Labs 1 & 3)
- **[Final] Sunny Bay Roastery - Sales Report** — an AI/BI dashboard over the metric view
- 10 fault report PDFs in a UC Volume
- `fault_reports_structured` table — the Lakeflow pipeline runs `ai_parse_document()`
  + `ai_extract()` across all 10 PDFs (used in Lab 2)
- `create_service_order` UC function

> **Prefer to run it by hand?** Open `bundle/src/notebooks/Lab 0 - Setup`, set the
> `catalog` widget (its first cell lists your options), and **Run All**. That builds the
> **maintenance** side only. The **sales** star schema, metric view, Sales Genie, and
> dashboard — plus `fault_reports_structured` — are built by the other tasks in the
> **"Agents in a Day - Setup"** job, so run that job to get the full workshop.

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
│   │   ├── job.yml             ← Setup job (maintenance + sales tasks)
│   │   ├── pipeline.yml        ← Lakeflow pipeline (parses + extracts all PDFs)
│   │   └── sales_pipeline.pipeline.yml ← Sales medallion pipeline (silver + gold)
│   └── src/
│       ├── data/               ← fault_reports/ PDFs + sales data-gen modules
│       ├── dashboards/         ← [Final] Sunny Bay sales dashboard (.lvdash.json)
│       ├── notebooks/
│       │   ├── Lab 0 - Setup.py         ← Maintenance setup (run via the job above)
│       │   ├── generate_data.ipynb      ← Generates the sales star schema
│       │   ├── deploy_metric_view.ipynb ← Builds the sales metric view
│       │   ├── deploy_genie_space.ipynb ← Pre-builds the Sales Genie
│       │   └── deploy_dashboard.py      ← Publishes the sales dashboard
│       └── transformations/
│           ├── fault_report_pipeline.py ← ai_parse_document + ai_extract
│           ├── silver/         ← sales silver transforms (dims + fact)
│           └── gold/           ← sales gold transforms (dims + fact)
├── labs/
│   ├── Lab 1 - Sara - Genie One.md
│   ├── Lab 2 - Document Intelligence.md
│   ├── Lab 3 - Build the Supervisor.md
│   ├── Lab 4 - Observe and Review.md
│   └── Lab 5 - AI Gateway and Write-back.md
│   (artifacts/ holds per-lab screenshots)
└── README.md
```
