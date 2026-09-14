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
| **Lab 2** | Marc | Manager analysis — `ai_parse_document()` + `ai_extract()` turn technicians' fault-report PDFs into insights |
| **Lab 3** | Marc | A **custom agent** deployed as a **Databricks App** with a human-in-the-loop approval gate; add durable **short-term memory on Lakebase** via the AI assistant, then observe with **MLflow traces** and a **Review App** |
| **Lab 4** | Tim (Platform) | Govern **reusable AI blocks** with the **AI Gateway** — a PII-blocking, rate-limited, logged model endpoint + an approval-gated you.com MCP tool; tested in the Playground |

## Prerequisites

- A Databricks workspace with **Unity Catalog** and **serverless compute** enabled, and a
  serverless **SQL warehouse** for Genie and the dashboard. Setup looks up
  **"Serverless Starter Warehouse"** (present on Free Edition), or you can set the
  Lab 0 setup notebook's `warehouse_id` widget. Setup does not start the warehouse.
- A region that supports **AI Functions** (`ai_parse_document`, `ai_extract`), **Agent
  Bricks** (Lab 2), **Databricks Apps** + a **Foundation Model serving endpoint** (Lab 3),
  and — for Lab 4 — the **Unity AI Gateway (Beta)**.
- Permission to **create a Unity Catalog catalog** (or an existing catalog you can write
  to). The Lab 0 setup notebook creates the catalog for you — default `sunny_bay_roastery` —
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

### Step 2 — Run the Lab 0 setup notebook

1. Open `labs/notebooks/Lab 0 - Setup` in the workspace.

   > To use a different catalog — e.g. on a shared workshop where everyone needs their
   > own — set the **`catalog`** widget at the top before running (default
   > `sunny_bay_roastery`). Nothing to pre-create: the notebook makes the catalog for you.

2. Click **Run all** (serverless — no cluster to pick). It creates the catalog and runs
   each setup step sequentially on the **same notebook compute**, using `%run`.
   No CLI installation, job run, or Lakeflow pipeline is needed. Wait for the
   final cell to finish; the last line prints **"🎉 All set."**


> [!NOTE]
> If you previously ran the pipeline-based setup, choose a fresh catalog. Lab 0
> detects streaming tables and materialized views and leaves them intact. Ordinary
> Delta tables created by the new setup can be rebuilt by rerunning it; existing
> `service_orders` are preserved. The old job and pipeline deployment code has been removed.

Lab 0 creates:

- `coffee_maintenance` schema with `machines`, `fault_events`, `service_orders`, and
  `location_managers` tables (the roster maps each location to its manager, used by Lab 3)
- `gold` sales star schema — `fact_coffee_sales` + `dim_store`/`dim_product`/`dim_customer`/`dim_date`
  (generated + transformed in the notebook, history from 2010)
- `gold.sm_fact_coffee_sales_genie` — a governed **metric view** over the star schema
- **Sunny Bay Sales Genie** — pre-built over the metric view (Labs 1 & 3)
- **[Final] Sunny Bay Roastery - Sales Report** — an AI/BI dashboard over the metric view
- 10 fault report PDFs in a UC Volume
- `fault_reports_structured` table — the notebook runs `ai_parse_document()`
  + `ai_extract()` across all 10 PDFs (used in Lab 2). Run `labs/setup/notebooks/build_fault_reports` again
  to process added or changed PDFs.
- `create_service_order` UC function
- **Lakebase** (autoscaling Postgres) for Lab 3's durable short-term memory — each participant
  uses their **own** project, set up by the `add-lakebase-short-term-memory` skill (no shared instance)

---

## Workshop Labs

All labs are **Databricks notebooks** in **`labs/notebooks/`**. Open the cloned Git
Folder and run **Lab 0 - Setup** first, then work through Labs 1 → 2 → 3 → 4.
Keep `labs/setup/` alongside `labs/notebooks/`; Lab 0 needs those supporting files. (See the *What you'll build* table above for the arc.)

---

## Repo structure

```
agents-in-a-day/
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
│   ├── setup/                    ← Lab 0 helpers and assets (keep alongside notebooks/)
│   │   ├── notebooks/            ← sales generation, table builds, Genie and dashboard setup
│   │   ├── data/                 ← sales helpers and fault-report PDFs
│   │   ├── dashboards/           ← sales dashboard template
│   │   ├── transformations/      ← batch silver/gold SQL
│   │   ├── batch_setup.py        ← loads sales SQL in dependency order
│   │   └── fault_report_transforms.py ← PDF parsing and extraction
│   ├── notebooks/                ← setup + four workshop labs
│   │   ├── Lab 0 - Setup.py      ← ⭐ Run this first
│   │   ├── Lab 1 - Genie One.py
│   │   ├── Lab 2 - Document Intelligence.py
│   │   ├── Lab 3 - Build the Custom Agent.py
│   │   └── Lab 4 - Unity Gateway and Write-back.py
│   ├── artifacts/                ← per-lab screenshots (referenced by the notebooks)
│   └── Deep Dives/               ← optional deep dives (e.g. Observability & Feedback)
└── README.md
```
