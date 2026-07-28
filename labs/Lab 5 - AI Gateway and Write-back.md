# 🔒 Lab 5 — Governed AI-Assisted Coding through the AI Gateway

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- Explore the **Unity AI Gateway** and understand what it governs.
- **(Admin)** Create a governed model serving endpoint with a **PII guardrail**, and
  grant workshop users access to it.
- Install the **opencode** AI coding agent and point it at the governed endpoint.
- **Vibe-code** the `create_service_order` write-back function through opencode — and
  watch a PII prompt get caught by the guardrail.
- See every call land in the **AI Gateway usage dashboard**.

## Introduction

So far every AI call — Genie queries, `ai_extract()`, the Supervisor — has flowed
through the **AI Gateway** without you thinking about it. In this final lab you put the
Gateway front and center and answer a question every platform team asks:

> *"Our developers want to use AI coding assistants. How do we let them — through **our**
> governed models, with **our** PII rules, and a full audit trail — instead of everyone
> pasting company code into random public tools?"*

The answer: serve a model behind the AI Gateway with guardrails, then point any
OpenAI-compatible tool (here, **opencode**) at it. Developers get their AI assistant;
the platform team gets governance. To make it concrete, you'll use that governed
assistant to **vibe-code the `create_service_order` write-back function** — the piece
that lets Marc's Supervisor turn a briefing into a real service order.

> [!NOTE]
> **Roles in this lab.** Steps 1–2 are done by a **workspace admin** (one person /
> the facilitator). Steps 3–5 are done by **every participant** on their own laptop.

---

## Instructions

### **Step 1: Explore the Unity AI Gateway (5 min)**

1. In the workspace sidebar, open **Serving** (Model Serving). This is where every
   model endpoint — foundation models, external models, and your agents — lives behind
   the **AI Gateway**.

2. Open any existing endpoint (for example `databricks-claude-sonnet-5`) and find the
   **AI Gateway** section. Note the controls the Gateway gives you on *any* endpoint:

   - **Usage tracking** — token counts, latency, and requester per call.
   - **Inference tables** — full request/response payload logging to Delta.
   - **AI Guardrails** — PII detection, safety, topic and keyword filtering.
   - **Rate limits** — per-user and per-endpoint request caps.

> [!NOTE]
> None of this requires changing model or application code. Governance is a property of
> the **endpoint**, applied at the Gateway — not something each developer has to wire in.

---

### **Step 2: (Admin) Create a governed endpoint with a PII guardrail (10 min)**

> [!IMPORTANT]
> This step is done **once, by a workspace admin**. Participants: watch, then use the
> endpoint your admin shares with you in Step 3.

1. In **Serving**, click **Create serving endpoint**.

2. **Name it** `workshop-governed-llm`.

3. **Served entity:** choose **Foundation models** → select a chat model
   (e.g. `databricks-claude-sonnet-5`, or a coding-tuned model like
   `databricks-gpt-5-3-codex`). This is pay-per-token — no external API key needed.

4. Expand **AI Gateway** and enable:

   - **Usage tracking** — ✅ On (so calls appear in the usage dashboard).
   - **AI Guardrails → PII detection** — set to **Block** (reject any request
     containing PII) or **Mask** (redact PII before it reaches the model).

5. Click **Create**. Wait for the endpoint to reach **Ready**.

6. **Grant participants access.** Open the endpoint → **Permissions** → grant your
   workshop users (or a group) **Can Query**. Share two things with the room:

   - The endpoint name: `workshop-governed-llm`
   - The workspace URL: `https://<your-workspace>.cloud.databricks.com`

> [!NOTE]
> **Why an admin-only step?** Creating endpoints and setting guardrails is a platform
> responsibility. Developers don't each configure PII rules — they *consume* a governed
> endpoint the platform team stands up once. That separation is the whole point.

---

### **Step 3: Install opencode and point it at the Gateway (10 min)**

Now each participant sets up an AI coding agent on their own laptop, backed by the
governed endpoint — not a public API.

1. **Install opencode** (see [opencode.ai](https://opencode.ai) for your OS):

   ```bash
   # macOS / Linux
   curl -fsSL https://opencode.ai/install | bash
   ```

2. **Create a Databricks personal access token (PAT)** to authenticate: in the
   workspace, **Settings → Developer → Access tokens → Generate new token**. Copy it.

3. **Export it** as an environment variable so it never gets committed:

   ```bash
   export DATABRICKS_TOKEN="dapi..."   # paste your PAT
   ```

4. **Point opencode at the governed endpoint.** Create `~/.config/opencode/opencode.json`:

   ```json
   {
     "$schema": "https://opencode.ai/config.json",
     "model": "databricks/workshop-governed-llm",
     "provider": {
       "databricks": {
         "npm": "@ai-sdk/openai-compatible",
         "name": "Databricks AI Gateway",
         "options": {
           "baseURL": "https://<your-workspace>.cloud.databricks.com/serving-endpoints",
           "apiKey": "{env:DATABRICKS_TOKEN}"
         },
         "models": {
           "workshop-governed-llm": { "name": "Workshop Governed LLM" }
         }
       }
     }
   }
   ```

   > Replace `<your-workspace>` with the URL your admin shared. The model ID
   > (`workshop-governed-llm`) is the **serving endpoint name** — Databricks exposes it
   > through an OpenAI-compatible API at `/serving-endpoints`.

5. **Confirm opencode sees it:**

   ```bash
   opencode models
   ```

   You should see `databricks/workshop-governed-llm` in the list.

---

### **Step 4: Vibe-code the write-back function with opencode (15 min)**

Now use your governed AI assistant to build something real: the **`create_service_order`**
Unity Catalog function — the write-back that lets Marc's Supervisor turn a briefing into
an actual service order. You'll *vibe-code* it through opencode instead of writing it by hand.

1. Start opencode in a scratch folder and describe what you need:

   ```
   Write a Databricks Unity Catalog SQL function
   `create_service_order(machine_id STRING, fault_code STRING, part_id STRING,
   technician_notes STRING)` that returns a STRING order id. It should INSERT a
   row into `<catalog>.coffee_maintenance.service_orders` with a generated
   order_id like 'SO-12345', current_timestamp(), and status 'pending', then
   return the order_id. Give me the CREATE FUNCTION statement.
   ```

   The answer comes back from **your governed Databricks endpoint** — not a public
   model. Governed, logged, rate-limited.

2. Iterate with opencode until the function looks right (ask it to add a `COMMENT` so an
   agent knows when to call it, or to handle quoting). Then run the generated
   `CREATE FUNCTION` in a SQL cell against your catalog and test it:

   ```sql
   SELECT <catalog>.coffee_maintenance.create_service_order(
     'CBM-003', 'E-07', 'SIE-EQ9-PUMP-003', 'Vibe-coded in Lab 5'
   ) AS order_id;
   ```

   > [!TIP]
   > **Fallback:** the Lab 0 setup job already registered a working
   > `create_service_order` function. If opencode's version gives you trouble or you're
   > short on time, just use the one from setup — it's ready to go.

3. Now trigger the **PII guardrail**. Send opencode a prompt containing obvious PII:

   ```
   Refactor this: customer John Smith, SSN 123-45-6789,
   email john.smith@example.com — store his record in a dict.
   ```

   - With PII = **Block**, the request is rejected before it reaches the model.
   - With PII = **Mask**, the PII is redacted before the model ever sees it.

> [!NOTE]
> The developer didn't configure anything. The guardrail lives on the endpoint, so it
> protects **every** tool that points at it — opencode today, something else tomorrow.
> You just built a real write-back function through an AI assistant that *cannot* leak PII.

---

### **Step 5: See it in the AI Gateway usage dashboard (5 min)**

1. Back in the workspace, open **Serving → `workshop-governed-llm` → Usage** (or the
   Gateway usage view / monitoring tab).

2. You'll see your opencode calls: request counts, input/output tokens, latency, and
   the requesting user — including the **blocked** PII request (surfaced as a rejected
   call).

3. **(Admin, optional)** For a workspace-wide view, query the system table directly in a
   SQL editor:

   ```sql
   SELECT
     date_trunc('hour', request_time) AS hour,
     requester,
     count(*)                         AS requests,
     sum(input_token_count)           AS input_tokens,
     sum(output_token_count)          AS output_tokens
   FROM system.serving.endpoint_usage
   WHERE endpoint_name = 'workshop-governed-llm'
   GROUP BY ALL
   ORDER BY hour DESC
   ```

> [!NOTE]
> This is the platform team's payoff: every AI coding call, from every developer,
> through governed models, with PII protection and full usage attribution — in one place.

---

## 🎉 Workshop Complete

**What you built today, on Databricks, zero infrastructure to provision:**

| | |
|---|---|
| **Sara** | Built a Genie space and got machine-health + sales answers from Genie One, enriched with live web knowledge — without touching the Lakehouse. |
| **Marc** | Turned PDF fault reports into structured data, built a multi-source Supervisor agent, and had domain experts review it through a Review App. |
| **Platform team** | Stood up a governed AI coding endpoint — PII guardrails, per-user usage, full audit — and vibe-coded the `create_service_order` write-back through it. |

**What you take home:**

- The Genie spaces and Supervisor — point them at your own data next week.
- The MLflow trace + Review App loop — the way to harden any agent with expert feedback.
- The governed AI Gateway endpoint pattern — bring AI coding assistants into your
  enterprise on *your* terms.

---

## What Happens Next?

- Drop a new PDF into `/Volumes/<catalog>/coffee_maintenance/fault_reports/`
  and watch it appear in `fault_reports_structured` automatically
  (the Lakeflow pipeline from Lab 0).

- Point opencode (or any OpenAI-compatible AI tool) at your governed endpoint for your
  own projects — same governance, your code.

> [!TIP]
> Ask your facilitator about follow-up deep-dive sessions on **Agent Bricks**,
> **Lakebase**, and **Databricks Apps**.
