# 🤖 Lab 3 — Build & Deploy Marc's Custom Agent

## 🎯 Learning Objectives

By the end of this lab you will be able to:

- See how a **custom agent** is packaged as a **Databricks App** — and that you can start
  one by cloning a template right from the Apps UI.
- Read and **modify the agent's control-flow code** (a LangGraph pipeline) and see your
  change take effect.
- **Deploy** the agent as an App and drive it — including a **human-in-the-loop approval
  gate** before it writes anything back.
- Inspect the agent's **MLflow trace** to debug what it did, step by step.
- Stand up a **Review App** so the people who do the job can grade real answers.

---

## 📖 Introduction

Sara manages one store. **Marc runs all 12.**

Labs 1–2 gave Marc the raw signal he needs, but not the decision:

- **Sara's Maintenance Genie (Lab 1)** — the governed, natural-language way to ask the
  machine/fault data *"which machines have unresolved faults, and what are the codes?"*
- **The field technicians' fault reports (Lab 2)** — the PDFs the techs write after a
  visit, turned into clean structured rows by Document Intelligence (`ai_parse_document` +
  `ai_extract`): which machine, which fault code, what happened.

On his own, Marc would still have to read every field report, cross-check each store's
revenue by hand, and decide store-by-store who to send a technician to first — every week,
across twelve locations.

> **What Marc's custom agent is for.** It does that legwork for him. It reads the field
> reports through Sara's Genie to find machines with unresolved faults, weighs each fault
> against the store's **revenue at risk**, and produces a **dispatch plan** — *a ranked
> shortlist of which machines to service this week, each with a draft message to that
> store's manager*. Marc reviews the plan and **approves** the ones worth acting on; only
> then does the agent raise the actual service order. **The manager keeps the judgement;
> the agent does the legwork.**

That last part — *the agent takes an action, but only after a human approves* — is the
thing a chat assistant can't do and why Marc needs a **custom agent**, not just a chatbot.

---

## What the dispatch plan is

The plan is the output of an explicit **LangGraph** pipeline — control flow you can read,
node by node:

```
assess → score → approval_gate ⇄ execute
                   (interrupt)   (create_service_order)

assess        → the Genies: which machines have unresolved faults, and each store's revenue
score         → plain Python: priority = 4·faults + revenue_at_risk/1000, then draft messages
approval_gate → LangGraph interrupt — PAUSES here until Marc approves a machine
execute       → create_service_order()  ← runs only after Marc approves
```

In the chat, the agent returns the result as a **ranked plan**: for each machine, its
location, the fault count and code, the revenue at risk, the priority score, and the
**draft message** to that store's manager. **The plan writes nothing.**
It is a recommendation until Marc approves a specific machine — which he does by simply
replying **"approve CBM-003"** in the same chat.

> [!NOTE]
> This app is built directly on the official
> [`agent-langgraph`](https://github.com/databricks/app-templates/tree/main/agent-langgraph)
> template — same `agent_server/` layout, same MLflow `ResponsesAgent` handlers, same
> built-in chat UI, same `mlflow.langchain.autolog()` tracing. **The only thing we changed
> is the agent itself:** instead of the template's generic tool-calling loop, it runs the
> explicit LangGraph pipeline above, with the approval gate. So what you learn here is the
> real template, not a bespoke fork.

---

## Instructions

### **Task 1: Explore custom agents on Apps (5 min)**

See where a custom agent app *comes from*. In the sidebar go to **Compute → Apps → Create
app → Start from a template**, and open the **LangGraph agent** template in the gallery —
an `agent_server/` Python backend plus a built-in chat UI. **You don't need to finish it;**
the point is to see that a custom agent is just an app you scaffold from this template.

Now open **`app/`** in this repo — it *is* that template, with Marc's agent inside it:

| File | What it is |
|---|---|
| `app/agent_server/dispatch.py` | The **LangGraph pipeline** — the control flow you'll edit in Task 2. |
| `app/agent_server/tools.py` | The **tool palette**: the two Genie spaces, the `create_service_order` UC function, and the location-manager roster. |
| `app/agent_server/agent.py` | The template's `ResponsesAgent` handlers — routes each message to *plan / explain / qa / approve*. |
| `app/app.yaml` | Config + resources (catalog, Genie space IDs, serving endpoint). |

---

### **Task 2: Modify one thing in the cloned template (10 min)**

Open **`app/agent_server/dispatch.py`** — this *is* the agent's brain. Read `build_graph()`:
the four nodes and their edges *are* the pipeline (`assess → score → approval_gate ⇄
execute`), and `approval_gate` calls `interrupt(...)` — the graph pauses there until your
"approve" resumes it. Now make **one small change** and see it show up later.

**Add a new control-flow element** — a node of your own. Add this function, then insert it
between `assess` and `score` (look for the `LAB 3 · TASK 2` marker in `build_graph()`):

```python
def note_fleet(state: PlanState) -> dict:
    """A simple pass-through node — it will appear as its own span in the trace."""
    print(f"[note] scoring {len(state['fleet'])} machines this run")
    return {}
```

```python
    # in build_graph(), register the node and re-route two edges:
    g.add_node("note_fleet", note_fleet)
    g.add_edge("assess", "note_fleet")   # was: assess → score
    g.add_edge("note_fleet", "score")
```

You've just changed the agent's control flow — in Task 5 you'll see `note_fleet` as a new
span in the trace.

> [!TIP]
> **Even simpler:** instead of a node, tweak the scoring policy at the `LAB 3 · TASK 2`
> marker (e.g. bump `REVENUE_WEIGHT` to `2.0` so a busy store outranks a fault-heavy quiet
> one) and watch the ranking change when you test in Task 4.

---

### **Task 3: Create and deploy the app — from the UI (10 min)**

No terminal, no config — do it all in the workspace UI.

1. **Get the code into your workspace.** In the sidebar: **Workspace → Create → Git folder**,
   paste this repo's URL, **Create**. (If your workshop workspace already has it, skip this.)

2. **Create the app.** **Compute → Apps → Create app → Custom**, name it
   `marc-dispatch-agent`, and point its **source code path** at the `app/` folder in your
   Git folder.

3. Click **Deploy** and wait for the app to reach **Running**.

That's it — the app ships in **sample-data mode**, so it deploys with nothing to wire up.

> [!NOTE]
> The agent runs on built-in Sunny Bay data, so there are **no resources to attach and no
> yaml to edit**. Wiring in your real Genie spaces and the governed `create_service_order`
> write-back is **Lab 4 (AI Gateway and Write-back)**.

---

### **Task 4: Test it out (5 min)**

Open the app URL — it's the template's chat UI. Work through what the agent can do:

| You say… | The agent… |
|---|---|
| **"Build my dispatch plan"** | runs the pipeline and returns the **ranked plan** |
| **"Why is CBM-003 ranked first?"** | explains the score straight from its own formula |
| **"What's the weekly revenue by store?"** | routes to the Sales Genie and answers |
| **"Approve CBM-003"** | executes the gated `create_service_order` write-back |

Read a flagged machine's **draft message** to its store manager (Sara, for Mission). Then
reply **"approve CBM-003"** — *now*, and only now, the agent resumes past the gate and
raises the service order (a simulated order ID in sample mode; Lab 4 makes it a real
governed write-back).

> [!NOTE]
> Nothing happened until you approved. That gate is the difference between an assistant
> that *answers* and an agent Marc trusts to *act*.

---

### **Task 5: Review the traces and MLflow experiment (7 min)**

Every message is logged as an **MLflow trace** — the full record of the routing and every
tool call.

1. In the sidebar open **Experiments**, and open the experiment **linked to your app** (the
   template wires it via `app.yaml`'s `MLFLOW_EXPERIMENT_ID`).

2. Click the **Traces** tab. Open a dispatch-plan trace and explore the **span waterfall** —
   one span per LangGraph node: `assess` → **`note_fleet`** (your Task 2 node!) → `score` →
   `approval_gate`.

3. Click a span to see its exact inputs and outputs — e.g. what the Genie tool returned, or
   the priority score the Python step computed.

> [!NOTE]
> This is how you debug an agent. Because the flow is explicit, the trace reads like the
> code — including the node you just added.

---

### **Task 6: Create a Review App (10 min)**

The loop that hardens an agent: real experts grade real output through a simple UI, and
every rating lands back on the trace.

1. **Create a label schema** — in your experiment open **Labeling → Labeling schemas →
   Create schema**, and add two:

   | Field | Quality rating | Correctness check |
   |---|---|---|
   | **Name** | `plan_quality` | `grounded_in_data` |
   | **Type** | Feedback · Categorical | Feedback · Categorical |
   | **Options** | `Poor`, `Fair`, `Good`, `Excellent` | `Yes`, `No` |
   | **Instruction** | *Is the ranking sensible and are the drafted messages ready to send?* | *Are the fault counts, revenue, and parts all supported by the data — nothing made up?* |

2. **Create a labeling session** — **Labeling → Labeling sessions → Create labeling
   session**. Name it `Sunny Bay — Dispatch Plan Review`, attach both schemas, and assign
   your reviewers.

3. From the **Traces** tab, select your traces → **Add to labeling session** → your session.

4. Open the session → **Share** → copy the **Review App URL** for your reviewers. Open it
   yourself: one plan at a time with your schema questions on the side. Rate it, submit.

5. Back in **Traces**, open a labeled trace — your feedback now appears under
   **Assessments**, attached to that exact trace.

> [!NOTE]
> That labeled feedback is what you'd later use to build an evaluation set or align an
> automated judge — so quality checks run continuously, not just once.

---

## 💡 Key takeaways

- **A custom agent is an app you can scaffold from a template** — a chat frontend, a Python
  backend, and the agent's logic running inside it.
- **The control flow is code you own.** The dispatch pipeline is ordered Python you can
  read, modify, and test — you changed a scoring weight and saw the ranking move.
- **The approval gate is the line between answering and acting.** It's a LangGraph
  `interrupt`, and it's why Marc trusts the agent with `create_service_order`.
- **The trace reads like the code.** One span per node means you debug by looking, not
  guessing.
- **The Review App closes the loop** — the people who do the job grade real output, and
  every rating lands back on the trace.

---

## What Happens Next?

Marc has a custom agent — deployed as an app, observable in MLflow, and reviewed by the
people who do the job. In the final lab you meet the **Unity AI Gateway** head-on and see
how the platform governs the AI *coding* that produced the write-back function.

➡️ Continue to **[Lab 4 — AI Gateway and Write-back](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
