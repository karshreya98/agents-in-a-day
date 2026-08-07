# Project Rules

## Project Context and Target Audience

This repository is a **hands-on workshop** ("Agents in a Day") for Databricks — a
4-hour workshop that adds an action layer to a Databricks workspace using Genie
agents, Agent Bricks, and the Unity AI Gateway. It is thematically a sequel to
**Dashboard in a Day (DAID)**, but it is fully self-contained: DAID's sales data engine,
medallion transformations, metric view, Sales Genie, and final dashboard are **vendored
into this bundle** (under `bundle/src/{data,transformations,dashboards,notebooks}`), and
the "Agents in a Day - Setup" job builds them alongside the maintenance data — so DAID
does not need to be installed separately. When editing sales assets, treat the vendored
DAID files as the source of truth here; do not reintroduce a separate DAID install or the
old flat `gold.sales` seed table.

- **Target audience:** Semi-technical business users and platform/AI admins,
  ranging from interns to leadership.
- Labs guide participants step-by-step through: building a Genie agent and driving it
  from Genie One (Lab 1); document intelligence with `ai_parse_document`/`ai_extract`
  (Lab 2); building a Multi-Agent Supervisor (Lab 3); observing it with MLflow traces
  and collecting expert feedback via a Review App (Lab 4); and governed AI-assisted
  coding through the Unity AI Gateway with `ucode`/OpenCode (Lab 5).
- Tone should be clear, encouraging, and beginner-friendly. Avoid jargon unless
  it is explained.
- **Platform:** Databricks with Unity Catalog + serverless compute (no clusters
  required). Works on Free Edition and standard workspaces.

## Lab File Structure

Each lab markdown file in `labs/` follows a consistent structure:

- **Title** — H1 heading with emoji and lab name.
- **Learning Objectives** — bulleted list of what participants will achieve.
- **Introduction** — brief explanation of the concept being taught.
- **Instructions** — the core of the lab, organized as:
  - **Bold Step headers** (e.g., `**Step 1: Do Something**`) — high-level milestones.
  - **Numbered tasks** under each step — specific actions the participant performs (1, 2, 3...)
  - **Screenshots** after relevant tasks using `<div><img></div>` blocks.
  - **Code blocks** with example SQL/Python when participants need to write code.
- **What Happens Next** — summary and transition to the next lab.

## Markdown Formatting Rules

- Each numbered task must be separated by a **blank line** so it renders as a distinct list item.
- After every `</div>` (screenshot block), add a **blank line** before the next numbered task.
- Screenshots use the pattern:
  ```html
  <div style="text-align:left;">
    <img src="./artifacts/LABNAME/FILENAME.png" width="XX%">
  </div>
  ```
- Code blocks use fenced triple backticks with a language tag (`sql`, `python`, `bash`).
- Use GitHub-style alerts for callouts:
  - `> [!NOTE]` — Highlights information that users should take into account, even when skimming.
  - `> [!TIP]` — Helpful advice for doing things better or more easily.
  - `> [!IMPORTANT]` — Crucial information necessary for users to succeed.
  - `> [!WARNING]` — Critical content demanding immediate user attention due to potential risks.
  - `> [!CAUTION]` — Advises about risks or negative outcomes of certain actions.
