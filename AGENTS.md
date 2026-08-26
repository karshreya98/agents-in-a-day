# Project Rules

## Project Context and Target Audience

- **Target audience:** Semi-technical business users and platform/AI admins,
  ranging from interns to leadership.
- Labs guide participants step-by-step through: building a Genie agent and driving it
  from Genie One (Lab 1); document intelligence / manager analysis with
  `ai_parse_document`/`ai_extract` (Lab 2); building a **custom agent** — a control-flow
  pipeline over Genie + web + a UC write-back — deploying it as a **Databricks App**, then
  observing it with MLflow traces and collecting expert feedback via a Review App (Lab 3);
  and governed reusable AI blocks through the Unity AI Gateway, with optional `ucode`/OpenCode (Lab 4).
- **Personas:** **Sara** is a location manager (Mission); **Marc** is the operations
  manager over all 12 locations. Field technicians (generic, unnamed) fill out the fault
  reports. Lab 3 teaches a **custom code agent** — an explicit LangGraph control-flow
  pipeline with a human-in-the-loop approval gate.
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
