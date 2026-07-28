# Agents in a Day 🤖

A hands-on 4-hour workshop that adds an **action layer** to your Databricks
workspace — built on top of **Dashboard in a Day**. Two characters, same Unity
Catalog, one day.

> **Prerequisite:** Complete **[Dashboard in a Day](https://github.com/DatabricksDashboardInADay/DatabricksDashboardInADay)**
> and run its setup job before starting here.

---

## How to get started

### Step 1 — Clone this repo as a Git Folder

1. In your Databricks workspace, go to **Workspace** (left sidebar).
2. Click **+ Add** → **Git Folder** (or **Add a Git Folder**).
3. Paste the repo URL: `https://github.com/<your-org>/agents-in-a-day`
4. Leave the defaults and click **Create Git Folder**.

The repo appears in your workspace as a folder you can browse like any notebook.

---

### Step 2 — Set your catalog name in `databricks.yml`

1. In your workspace, open the repo folder → `bundle/` → `databricks.yml`.
2. Change the `catalog` variable to match what you used in DAID:

```yaml
variables:
  catalog:
    default: sunny_bay_roastery   # ← change this if needed
```

3. Save the file.

> **Not sure which catalog to use?**
> Open `labs/Lab 0 - Setup`, run the catalog picker cell (cell 3),
> then come back and update `databricks.yml`.

---

### Step 3 — Deploy the bundle

1. With `databricks.yml` open, click **Deploy** (button in the top-right toolbar).
2. Databricks validates the bundle and creates the job resource.
3. You should see a green **"Bundle deployed successfully"** message.

---

### Step 4 — Start the setup job

1. In the left sidebar go to **Workflows**.
2. Find **"Agents in a Day — Setup"** and click it.
3. Click **Run now**.
4. The job runs `Lab 0 - Setup` which creates all tables, the fault report PDFs,
   and the `create_service_order` UC function.
5. Wait for the green **Succeeded** badge (~2 min).

---

### Step 5 — Open Lab 0 and Run All

1. Open `labs/Lab 0 - Setup` in the workspace.
2. Confirm `catalog` in cell 2 matches your catalog.
3. Click **Run All Below** from cell 2.
4. The summary at the bottom confirms everything is ready.

---

## Workshop Labs

| Lab | Character | What you build |
|-----|-----------|----------------|
| **Part 1** | Sara | Genie One + you.com MCP — briefings without touching data |
| **Lab 1** | Marc | Document Intelligence — `ai_extract()` on fault report PDFs |
| **Lab 2** | Marc | Build the Supervisor — Agent Bricks multi-source agent |
| **Lab 3** | Marc | Share, Test, and Harden — test scenarios + guardrails |
| **Lab 4** | Marc | AI Gateway + write-back — `create_service_order` UC function |

All labs are in the `labs/` folder. Open them as markdown files to follow along.

---

## Repo structure

```
agents-in-a-day/
├── bundle/
│   ├── databricks.yml          ← Set your catalog here, then Deploy
│   └── resources/
│       └── job.yml             ← Setup job definition
├── labs/
│   ├── Lab 0 - Setup.py        ← Notebook: creates all tables + PDFs + UC function
│   ├── Part 1 - Sara - Genie One.md
│   ├── Lab 1 - Document Intelligence.md
│   ├── Lab 2 - Build the Supervisor.md
│   ├── Lab 3 - Share and Test.md
│   └── Lab 4 - AI Gateway and Write-back.md
└── README.md
```
