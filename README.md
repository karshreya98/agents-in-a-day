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
| **Lab 1** | Sara | A **Maintenance Genie** agent, driven from Genie One alongside the pre-built Sales Genie, enriched with a you.com MCP tool |
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
- Permission to **create a Unity Catalog catalog** (or an existing catalog you can write
  to). The bootstrap notebook creates the catalog for you — default `sunny_bay_roastery` —
  and seeds all the data, so there's no other workshop to install. If catalog creation is
  restricted on your workspace, set the notebook's `catalog` widget to one an admin already
  made (it falls back to using the existing catalog).
- **Lab 5 only:** an account admin must enable the **Unity AI Gateway (Beta)** and
  **Managed MCP Servers** previews (account console → Previews). Participants install
  [`ucode`](https://github.com/databricks/ucode) + [OpenCode](https://opencode.ai) locally.

> Running this for a group? See each lab's admin/prerequisite callouts — one admin
> registers the you.com MCP service, governs a model for Lab 5, and grants participants
> access. Give each participant their own catalog so their tables don't collide.

---

## Getting started

**Clone as a Git Folder, then open the bootstrap notebook and Run All — that's it.**
No local CLI, no catalog to pre-create, nothing to click in Workflows. The bootstrap
notebook creates the catalog, deploys the bundle, and runs the setup job for you — one
run builds everything the labs need: the maintenance tables, the Sunny Bay sales star
schema and metric view, a pre-built Sales Genie and dashboard, the fault-report PDFs, and
the `fault_reports_structured` table (via a Lakeflow pipeline).

### Step 1 — Clone this repo as a Git Folder

1. In your Databricks workspace go to **Workspace** (left sidebar)
2. Click **+ Add** → **Git Folder**
3. Paste: `https://github.com/karshreya98/agents-in-a-day`
4. Click **Create Git Folder**

---

### Step 2 — Run the bootstrap notebook

1. Open `bundle/src/notebooks/bootstrap` in the workspace.

   > To use a different catalog — e.g. on a shared workshop where everyone needs their
   > own — set the **`catalog`** widget at the top before running (default
   > `sunny_bay_roastery`). Nothing to pre-create: the notebook makes the catalog for you.

2. Click **Run all** (serverless — no cluster to pick). It creates the catalog, deploys
   the bundle, then runs the **"Agents in a Day - Setup"** job end-to-end. Wait for the
   final cell to finish (~15–20 min); the last line prints **"🎉 All set."**

> **Why a bootstrap notebook and not just "Deploy the bundle"?** A Lakeflow pipeline's
> target `catalog` is validated by Unity Catalog **at bundle-deploy time**, which is
> earlier than any job task could create it — so the catalog must exist *before* deploy.
> On Free Edition / Default-Storage workspaces the catalog can only be made with SQL
> `CREATE CATALOG` (the catalog REST API needs a storage root that isn't there). The
> bootstrap notebook runs the SQL create first, then deploys — one ordered, one-click,
> Free-Edition-safe path. It installs the Databricks CLI on the serverless notebook and
> deploys/runs the bundle using your own workspace credentials.

The bootstrap creates:
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

> **Just want the maintenance tables?** Open `bundle/src/notebooks/Lab 0 - Setup`, set the
> `catalog` widget to a catalog you can write to (it must already exist), and **Run All**.
> That builds the **maintenance** side only. The **sales** star schema, metric view, Sales
> Genie, and dashboard — plus `fault_reports_structured` — are built by the rest of the
> **"Agents in a Day - Setup"** job, so run the bootstrap notebook to get the full workshop.

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
│   ├── databricks.yml          ← Default catalog name (bootstrap can override it)
│   ├── resources/
│   │   ├── job.yml             ← Setup job (maintenance + sales tasks)
│   │   ├── pipeline.yml        ← Lakeflow pipeline (parses + extracts all PDFs)
│   │   └── sales_pipeline.pipeline.yml ← Sales medallion pipeline (silver + gold)
│   └── src/
│       ├── data/               ← fault_reports/ PDFs + sales data-gen modules
│       ├── dashboards/         ← [Final] Sunny Bay sales dashboard (.lvdash.json)
│       ├── notebooks/
│       │   ├── bootstrap.py             ← ⭐ Run this: creates catalog, deploys, runs setup
│       │   ├── Lab 0 - Setup.py         ← Maintenance setup (run by the setup job)
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
