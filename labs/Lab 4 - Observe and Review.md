# 🔗 Lab 4 — Observe, Review, and Get Expert Feedback

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- Share the Supervisor with a colleague directly from the Agent Bricks UI.
- Inspect the Supervisor's **MLflow traces** to see exactly how it reasoned and which
  tools it called.
- Create a **label schema** so domain experts rate answers consistently.
- Launch a **labeling session** and share a **Review App** link so non-technical
  experts (like Sara and Marc) can give structured feedback — all in the UI.

## Introduction

Marc's Supervisor is live. Before Sunny Bay trusts it, two questions matter:

1. **Can we see what it did?** When the Supervisor answers, which sub-agents did it
   call, in what order, and how long did each take? MLflow **traces** answer this — and
   Agent Bricks logs them automatically.
2. **Do the experts agree it's good?** An answer that *looks* right isn't enough. You
   need Marc and Sara — the people who actually do the job — to grade real answers. The
   **Review App** lets them do that with no Databricks knowledge, guided by a **label
   schema** you define.

This lab is done entirely in the UI. No code.

---

## Instructions

### **Step 1: Share the Supervisor (2 min)**

The Supervisor you built in Lab 3 already has a shareable URL — no deployment step needed.

1. In the workspace sidebar, navigate to **Agents** → **Supervisor Agents**.

2. Open your **Marc Maintenance Supervisor**.

3. Click the **Share** button (top-right of the chat UI).

4. Copy the link and open it in an incognito tab, or paste it to a colleague in the room.

> [!NOTE]
> Anyone with the link who has workspace access can immediately chat with the
> Supervisor using their own identity — no extra configuration.

---

### **Step 2: Generate a few traces to review (5 min)**

You can only review answers that exist — so run a few realistic questions first. In the
Supervisor chat, ask each of these (they exercise different tools):

**Multi-source read:**
```
I'm visiting CBM-003 in Mission District tomorrow. Give me a full briefing:
fault history, pressure trends from the reports, and what parts to bring.
```

**Web lookup:**
```
Are there known manufacturer advisories for E-07 pressure faults on the
Siemens EQ.9 Plus Connect?
```

**Out-of-scope (a question it should decline):**
```
What is the current Siemens stock price?
```

> [!TIP]
> Vary the machines (try CBM-009 too) so your reviewers see a mix of answers, not five
> copies of the same one.

---

### **Step 3: Inspect the MLflow traces (8 min)**

Every Supervisor call is automatically logged as an **MLflow trace** — a full record of
the reasoning and every tool call.

1. In the workspace sidebar, open **Experiments** (under **Machine Learning** /
   **MLflow**).

2. Find and open the experiment tied to your Supervisor — it shares the agent's name
   (e.g. *Marc Maintenance Supervisor*).

3. Click the **Traces** tab. You'll see one row per question you asked, with columns for
   **Request**, **Response**, **Execution time**, **State**, and **Assessments**.

4. Click the CBM-003 trace to open it. Explore:
   - **Summary** — the top-level request and final response.
   - **Details / Timeline** — the span waterfall showing each sub-agent call
     (Maintenance Genie → you.com for the CBM-003 question), how long each took, and the
     exact inputs and outputs at every step.

> [!NOTE]
> This is how you debug an agent. If a briefing missed the PDF pressure readings, the
> trace shows *whether the Maintenance Genie was even called* — you're never guessing.

5. Try a filter: in the trace list, filter **State = ERROR** (or the out-of-scope
   question) to see how the Supervisor handled the edge case.

---

### **Step 4: Create a label schema (5 min)**

A **label schema** is the question set your domain experts answer for each trace. It
keeps feedback consistent across reviewers.

1. Still in your experiment, open the **Labeling** area and choose **Labeling schemas**
   → **Create schema**.

2. Create a **feedback** schema for overall quality:

   | Field | Value |
   |---|---|
   | **Name** | `answer_quality` |
   | **Type** | Feedback |
   | **Input type** | Categorical |
   | **Options** | `Poor`, `Fair`, `Good`, `Excellent` |
   | **Instruction** | `Rate this briefing as if you were the technician receiving it. Is it accurate, complete, and actionable?` |
   | **Enable comment** | ✅ On (let experts explain their rating) |

3. Create a second schema to catch hallucinations:

   | Field | Value |
   |---|---|
   | **Name** | `grounded_in_data` |
   | **Type** | Feedback |
   | **Input type** | Categorical |
   | **Options** | `Yes`, `No` |
   | **Instruction** | `Are all fault codes, pressure readings, and part numbers in the answer actually supported by Sunny Bay's data — with nothing made up?` |

> [!TIP]
> Mix a **rating** schema (subjective quality) with a **yes/no** schema (a hard
> correctness check). Short scales keep reviewers fast; the comment box captures the *why*.

---

### **Step 5: Launch a labeling session and Review App (7 min)**

A **labeling session** bundles a set of traces with your schemas and hands reviewers a
simple **Review App** — no Databricks skills required.

1. In the **Labeling** area, choose **Labeling sessions** → **Create labeling session**.

2. Configure it:

   | Field | Value |
   |---|---|
   | **Name** | `Marc & Sara — Supervisor Review` |
   | **Label schemas** | Select both `answer_quality` and `grounded_in_data` |
   | **Assigned users** | Add your domain experts' emails (e.g. Marc, Sara, or a colleague in the room) |

3. Add traces to the session: go back to the **Traces** tab, **select** the traces from
   Step 2/3, and choose **Add to labeling session** → your new session. (You can also add
   traces from within the session.)

4. Open the session and click **Share** to copy the **Review App URL**. Send it to your
   assigned reviewers.

---

### **Step 6: Review as a domain expert (5 min)**

Put yourself in Marc's shoes — open the Review App link you just shared.

1. The Review App shows one trace at a time: the **question**, the Supervisor's
   **answer**, and your schema questions on the side. No SQL, no traces, no jargon.

2. For each answer, pick a rating for `answer_quality`, answer `grounded_in_data`, and
   add a comment where useful.

3. Submit and move to the next one.

4. Back in the experiment's **Traces** tab, open a trace you labeled — your feedback now
   appears under **Assessments**, attached to that exact trace.

> [!NOTE]
> This is the loop that hardens an agent: real experts grade real answers through a
> friendly UI, and every rating lands back on the trace. That labeled feedback is what
> you'd later use to build an evaluation dataset or align an automated LLM judge — so
> quality checks run continuously without pulling an expert in every time.

---

## ✅ Lab 4 Done

You now have a Supervisor that is:
- **Shareable** — a URL ready to hand to Marc.
- **Observable** — every answer traced end-to-end in MLflow, tool calls and all.
- **Reviewable** — a label schema and Review App so domain experts give structured
  feedback that attaches to each trace.

In Lab 5 you give Marc the ability to *act* — not just read.

➡️ Continue to **[Lab 5 — AI Gateway and Write-back](./Lab%205%20-%20AI%20Gateway%20and%20Write-back.md)**
