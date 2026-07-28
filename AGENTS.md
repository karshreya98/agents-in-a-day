# Project Rules

## Project Context and Target Audience

This repository is a **hands-on workshop** ("Agents in a Day") for Databricks — a
4-hour sequel to **Dashboard in a Day (DAID)**. It picks up where DAID left off and
adds the action layer using Agent Bricks, Genie One, and Databricks Apps.

- **Target audience:** Semi-technical business users and platform/AI admins who
  attended (or have the DAID assets deployed), ranging from interns to leadership.
- Labs guide participants step-by-step through document intelligence, building a
  Multi-Agent Supervisor, wiring conversation memory via Lakebase, and closing
  the loop with AI Gateway + write-back.
- Tone should be clear, encouraging, and beginner-friendly. Avoid jargon unless
  it is explained.
- **Platform:** Databricks Free Edition (no clusters required; all compute is serverless).

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
