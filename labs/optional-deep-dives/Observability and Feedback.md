# 🔬 Observability and Feedback

> Pairs with **[Lab 3 — Build & Deploy Marc's Custom Agent](../Lab%203%20-%20Build%20%26%20Deploy%20Marc's%20Custom%20Agent.md)**.
> Do Lab 3 first, then come here to see *inside* the agent and build the loop that hardens it.

## What you'll do

1. **Generate the agent's traces** and read the **span waterfall** — the routing, every node, every tool call.
2. **Add an LLM-as-a-judge scorer** that grades every trace automatically, from the UI.
3. **Collect human feedback** with a **Review App**, from the UI.

## Key concepts

| Term | What it means here |
|---|---|
| **Trace / span waterfall** | One run of the agent, broken into nested steps (nodes, tool calls). The waterfall is that tree in the UI. |
| **Scorer** | An automated grade on each trace — here an **LLM-as-a-judge** that reads the trace and scores it. |
| **Review App** | A UI for experts to label traces (thumbs, comments) so you can improve the agent from real feedback. |

---

## ⚠️ Free Edition vs. paid — read first

A trace has a lightweight **record** (request, response, latency, status — saved via the API) and heavier **span data** (the waterfall — saved to storage). Where the span data can be written depends on *who produces the trace*:

| Traces produced by… | Free Edition | Paid / managed-storage workspace |
|---|---|---|
| **A notebook** (Task 1 here) | ✅ full waterfall | ✅ full waterfall |
| **A deployed Databricks App** | ⚠️ record only — no waterfall | ✅ full waterfall (via Unity Catalog) |

A deployed app on Free Edition can't ship its span data (its sandbox can't reach trace storage, and UC trace tables need managed storage Free Edition lacks) — so you'll see *"No trace data available."* A **notebook** runs outside that sandbox and works everywhere, so **Task 1 uses a notebook.** Everything after works the same regardless of how the traces got there.

---

## Task 1 — Generate & review traces

**Get traces into an experiment — pick your path:**

- **Any workspace (recommended, always works):** open the ready notebook
  **[`explore_agent_traces.py`](./explore_agent_traces.py)**, paste your Git-folder `app/` path
  where marked, and **Run All**. It drives the dispatch agent and logs the traces to the
  experiment **`/Shared/dispatch-agent-observability`**.
- **Managed-storage workspace only — skip the notebook:** your **deployed app** already logs
  traces to Unity Catalog (wired in `app.yaml` → `/Shared/marc-dispatch-agent`,
  `sunny_bay_roastery.gold`). Just chat with the app from Lab 3 and use that experiment. One
  one-time grant is required first — see the note below.

**Review the trace:**

1. Sidebar → **Experiments** → open your experiment → **Traces** tab.
2. Open the **"Build my dispatch plan"** trace → **See detailed trace view**.
3. Walk the waterfall top to bottom — it *is* the agent's control flow:
   - **`dispatch_agent`** → the whole message.
   - **`assess`** → expand it: the **Genie tool calls** and the roster lookup, each with its
     exact inputs/outputs (click a span) — proof of what the agent asked and got back.
   - **`score`** → the deterministic priority ranking · **`approval_gate`** → where it paused
     for a human. (The **approve** message adds `execute → create_service_order`, the gated
     write-back.)
   - Each span shows **latency** and **status** — this is how you debug a slow or wrong answer.

> [!NOTE]
> **Managed-storage deployed-app path only** — grant the app's service principal write access
> to the trace schema *before its first deploy* (the app writes as its SP, and UC links the
> experiment on startup). Copy the app's **App ID** from its page, then run once in a SQL editor:
> ```sql
> GRANT USE CATALOG ON CATALOG sunny_bay_roastery TO `<APP_ID>`;
> GRANT USE SCHEMA, CREATE TABLE, MODIFY, SELECT ON SCHEMA sunny_bay_roastery.gold TO `<APP_ID>`;
> ```
> On Free Edition this won't take (default-storage catalog) — use the notebook path instead.

---

## Task 2 — Add an LLM-as-a-judge scorer (UI)

A trace tells you *what happened*; a **judge** tells you *whether it was any good* — automatically, so you don't read every trace by hand. An LLM-as-a-judge scores each trace against a criterion you write in plain English.

1. In your experiment, open the **Evaluation → Judges / Scorers** area → **Create judge**.
2. Choose a **custom LLM judge** and give it a plain-language **guideline**, e.g.:
   > *"The dispatch plan ranks machines sensibly — more unresolved faults and higher
   > revenue-at-risk should rank higher — and each drafted manager message is specific and
   > ready to send."*
3. Run it over your traces. The judge model reads each trace and records a **pass/fail with a
   rationale** as an assessment on the trace — visible in the **Assessments** panel.

> [!NOTE]
> Databricks also ships **built-in judges** (relevance, safety, groundedness, …) you can enable
> the same way. Automated judges are how you keep score as the agent changes — run them on every
> new version and watch the pass rate.

---

## Task 3 — Collect human feedback with a Review App (UI)

Judges scale; humans set the bar. A **Review App** lets the people who own the outcome — Marc,
the store managers — grade real output, and every rating attaches to the exact trace.

1. In your experiment: **Labeling → Labeling schemas → Create schema**. Add:
   - `plan_quality` — rating *Poor / Fair / Good / Excellent*: *"is the ranking sensible and are
     the drafted messages ready to send?"*
   - `grounded_in_data` — *Yes / No*: *"are the fault counts, revenue, and parts all supported
     by the data?"*
2. **Labeling → Labeling sessions → Create labeling session**, name it
   `Sunny Bay — Dispatch Plan Review`, attach both schemas, assign reviewers.
3. From **Traces**, select your traces → **Add to labeling session**.
4. Open the session → **Share** → copy the **Review App URL**. Open it, rate a plan, submit —
   the feedback lands under **Assessments** on that exact trace.

> [!NOTE]
> That labeled set is your **eval dataset** and the seed for tuning the judge from Task 2 — so
> the next version of the agent is measured, not guessed at.

---

## 💡 Key takeaways

- **A trace is the agent's control flow, replayable** — root → nodes → tool calls, each with
  inputs, outputs, latency, and status.
- **Where span data lands depends on the producer** — notebooks work everywhere; a deployed app
  needs managed storage (Unity Catalog), which Free Edition doesn't have.
- **Two graders, one loop** — an **LLM judge** scores every trace automatically, **human review**
  sets the standard, and both attach to the trace as the raw material for eval and improvement.
