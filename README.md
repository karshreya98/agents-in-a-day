# Agents in a Day 🤖

A hands-on 4-hour workshop that adds an **action layer** to your Databricks
workspace.

Two personas at a fictional coffee-machine operator, **Sunny Bay Roastery**:
**Sara** (a location manager who just wants answers) and **Marc** (the operations manager
over all 12 locations, who has to decide and act). Across four labs you turn governed data
+ unstructured PDFs into Genie agents, a **custom agent deployed as a Databricks App** with
human-feedback review, and governed AI-assisted coding — all on Databricks, no
infrastructure to provision.

## What you'll build

| Lab | Persona | What you build |
|-----|---------|----------------|
| **Lab 1** | Sara | A **Maintenance Genie** agent, driven from Genie One alongside the pre-built Sales Genie, enriched with a you.com MCP tool |
| **Lab 2** | Marc | Manager analysis — `ai_parse_document()` + `ai_extract()` turn technicians' fault-report PDFs into a table |
| **Lab 3** | Marc | A **custom agent** deployed as a **Databricks App** with a human-in-the-loop approval gate; add durable **short-term memory on Lakebase** via the AI assistant, then observe with **MLflow traces** and a **Review App** |
| **Lab 4** | Tim (Platform) | Govern **reusable AI blocks** with the **AI Gateway** — a PII-blocking, rate-limited, logged model endpoint + an approval-gated you.com MCP tool; tested in the Playground |

## Prerequisites

- A Databricks workspace with **Unity Catalog** and **serverless compute** enabled, and a
  running serverless **SQL warehouse**. The bundle looks this warehouse up by name —
  it defaults to **"Serverless Starter Warehouse"** (present on Free Edition). On a shared
  workspace with a different name, update the `warehouse_id` lookup in `bundle/databricks.yml`.
- A region that supports **AI Functions** (`ai_parse_document`, `ai_extract`) (Lab 2),
  **Databricks Apps** (Lab 3), and — for Lab 4 — the **Unity AI Gateway (Beta)** plus a
  **Foundation Model serving endpoint**.
- Permission to **create a Unity Catalog catalog** (or an existing catalog you can write
  to). The bootstrap notebook creates the catalog for you — default `sunny_bay_roastery` —
  and seeds all the data, so there's no other workshop to install. If catalog creation is
  restricted on your workspace, set the notebook's `catalog` widget to one an admin already
  made (it falls back to using the existing catalog).
- **Lab 4 only:** admin rights to create a **model serving endpoint** and configure its
  **AI Gateway** guardrails, plus the **you.com MCP** connection (registered in Lab 1). It's
  all UI-driven and Free-Edition friendly. The `ucode` coding-agent step is an optional
  **bonus** that needs a non-Free workspace.

> Not using Free Edition or have not admin rights on your environment? See each lab's admin/prerequisite callouts — one admin
> registers the you.com MCP service, governs a model for Lab 4, and grants participants
> access. Give each participant their own catalog so their tables don't collide.

---

## Getting started

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


The bootstrap creates:
- `coffee_maintenance` schema with `machines`, `fault_events`, `service_orders`, and
  `location_managers` tables (the roster maps each location to its manager, used by Lab 3)
- `gold` sales star schema — `fact_coffee_sales` + `dim_store`/`dim_product`/`dim_customer`/`dim_date`
  (generated + transformed by the sales pipeline, history from 2010)
- `gold.sm_fact_coffee_sales_genie` — a governed **metric view** over the star schema
- **Sunny Bay Sales Genie** — pre-built over the metric view (Labs 1 & 3)
- **[Final] Sunny Bay Roastery - Sales Report** — an AI/BI dashboard over the metric view
- 10 fault report PDFs in a UC Volume
- `fault_reports_structured` table — the Lakeflow pipeline runs `ai_parse_document()`
  + `ai_extract()` across all 10 PDFs (used in Lab 2)
- `create_service_order` UC function

---

## Workshop Labs

All labs are step-by-step markdown in the **`labs/`** folder — start with
**[Lab 1 — Sara: From Dashboard to Action](labs/Lab%201%20-%20Sara%20-%20From%20Dashboard%20to%20Action.md)**
and follow the ➡️ links at the bottom of each. (See the *What you'll build* table above
for the arc.)

- [Lab 1 — Sara: From Dashboard to Action](labs/Lab%201%20-%20Sara%20-%20From%20Dashboard%20to%20Action.md)
- [Lab 2 — Document Intelligence](labs/Lab%202%20-%20Marc%20-%20Document%20Intelligence.md)
- [Lab 3 — Build & Deploy Marc's Custom Agent](labs/Lab%203%20-%20Build%20%26%20Deploy%20Marc's%20Custom%20Agent.md)
- [Lab 4 — Govern Reusable AI Blocks](labs/Lab%204%20-%20Govern%20Reusable%20AI%20Blocks.md)
- [Optional: Observability & Feedback](labs/optional-deep-dives/Observability%20and%20Feedback.md)

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
├── app/                        ← Lab 3: Marc's agent on the agent-langgraph template
│   ├── app.yaml                ← Databricks App config (Genie space IDs, serving endpoint)
│   ├── agent_server/
│   │   ├── dispatch.py         ← LangGraph StateGraph: control flow + approval interrupt + scoring
│   │   ├── tools.py            ← Genie spaces, create_service_order, location roster
│   │   ├── agent.py            ← template ResponsesAgent handlers (routes plan/explain/qa/approve)
│   │   └── start_server.py, utils.py ← unchanged from the template
│   ├── scripts/                ← template quickstart / start-app / deploy helpers
│   └── tests/                  ← offline dry-run smoke tests (AGENT_DRY_RUN=1)
├── labs/
│   ├── Lab 1 - Sara - From Dashboard to Action.md
│   ├── Lab 2 - Marc - Document Intelligence.md
│   ├── Lab 3 - Build & Deploy Marc's Custom Agent.md  ← deploy the agent app + Lakebase memory
│   ├── Lab 4 - Govern Reusable AI Blocks.md           ← AI Gateway model + MCP blocks
│   ├── optional-deep-dives/Observability and Feedback.md
│   └── artifacts/                    ← per-lab screenshots
└── README.md
```
