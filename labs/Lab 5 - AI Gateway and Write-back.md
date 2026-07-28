# 🔒 Lab 5 — Governed AI-Assisted Coding through the AI Gateway

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- Explore the **Unity AI Gateway** (Beta) and understand what it governs.
- **(Admin)** Register a governed model service, attach a **PII guardrail** (service
  policy), and grant workshop users access.
- Install **`ucode`** — Databricks' launcher that routes coding agents (Claude Code,
  Codex, Gemini CLI…) through the Unity AI Gateway with no API keys.
- **Vibe-code** the `create_service_order` write-back function through a governed
  coding agent — and watch a PII prompt get caught by the guardrail.
- See every call land in the **Coding Agents usage dashboard**.

## Introduction

So far every AI call — Genie queries, `ai_extract()`, the Supervisor — has been governed
by Databricks. In this final lab you meet the **Unity AI Gateway (Beta)** head-on and
answer a question every platform team asks:

> *"Our developers want to use AI coding assistants. How do we let them — through **our**
> governed models, with **our** PII rules, and a full audit trail — instead of everyone
> pasting company code into random public tools?"*

The Unity AI Gateway is Databricks' governance layer for the *runtime* interactions
between models, agents, MCP servers, and tools — built on Unity Catalog. The answer:
register a model service, attach guardrails, then route any coding agent through it with
**`ucode`** (Databricks' Unity AI Gateway coding CLI — [github.com/databricks/ucode](https://github.com/databricks/ucode)).
Developers get their favorite assistant; the platform team gets governance and no leaked
API keys. To make it concrete, you'll use that governed assistant to **vibe-code the
`create_service_order` write-back function** — the piece that lets Marc's Supervisor turn
a briefing into a real service order.

> [!NOTE]
> **Roles in this lab.** Steps 1–2 are done by a **workspace admin** (one person /
> the facilitator). Steps 3–5 are done by **every participant** on their own laptop.

> [!IMPORTANT]
> Unity AI Gateway is in **Beta**. An account admin must enable it from the account
> console **Previews** page ("Manage Databricks previews") before this lab. Beta features
> incur no charges during the preview.

---

## Instructions

### **Step 1: Explore the Unity AI Gateway (5 min)**

1. In the workspace sidebar, open **Unity AI Gateway** (under **Govern**). Unlike the
   old per-endpoint model-serving gateway, this is a single **control plane** where AI
   services — foundation models, MCP servers, tools, and agents — are registered as
   governed Unity Catalog objects.

2. Look around. Note the four things the Gateway governs for *any* registered service:

   - **Access control** — grant/revoke with standard Unity Catalog privileges.
   - **Service policies (guardrails)** — inspect request/response content; PII detection,
     safety, allow/deny rules.
   - **Traffic management** — rate limits, budgets with per-user caps, failover.
   - **Monitoring** — usage, cost attribution by principal/model/tag, request logging.

> [!NOTE]
> The shift from the old gateway: governance is no longer bolted onto each serving
> endpoint — it's centralized in Unity Catalog and covers the *runtime interactions*
> between models, agents, tools, and MCP servers.

---

### **Step 2: (Admin) Register a governed model service with a PII guardrail (10 min)**

> [!IMPORTANT]
> This step is done **once, by a workspace admin** (with the Beta preview enabled).
> Participants: watch, then use the model service your admin shares with you in Step 3.

1. In **Unity AI Gateway**, open **Models** (model services) → **Register / Create**.

2. **Name it** `workshop-governed-llm` and back it with a Databricks foundation model
   (e.g. `databricks-claude-sonnet-5`, or a coding-tuned model such as
   `databricks-gpt-5-3-codex`). Pay-per-token — no external API key needed.

3. Turn on **Usage tracking** and **Inference tables** so calls are logged and auditable.

4. Attach a **PII guardrail**. Open the service's **Policies** tab → **New policy** →
   choose the **built-in PII guardrail** and set the mode:

   - **Sanitize / Mask** — redact PII before it reaches the model (recommended for the
     demo — the coding task still succeeds, the PII just never leaves the Gateway).
   - **Block** — reject any request containing PII outright.

   Pick the recommended evaluator model when prompted.

   > [!NOTE]
   > In Beta, use the **built-in** PII guardrail for redaction. Custom service policies
   > (SQL UDFs) return ALLOW/DENY/ASK decisions but don't rewrite content — great for
   > access rules, not for sanitization.

5. **Grant participants access.** On the model service, use **Permissions** (Unity
   Catalog privileges) to grant your workshop users (or a group) query access. Share the
   workspace URL and the service name (`workshop-governed-llm`) with the room.

> [!NOTE]
> **Why an admin-only step?** Registering services and attaching guardrails is a platform
> responsibility. Developers don't each configure PII rules — they *consume* a governed
> service the platform team stands up once. That separation is the whole point.

---

### **Step 3: Install `ucode` and route a coding agent through the Gateway (10 min)**

Now each participant sets up an AI coding agent on their own laptop — routed through the
governed Gateway, with **no API keys** to manage. `ucode` is Databricks' launcher: it
runs Claude Code, Codex, Gemini CLI, and others *through* the Unity AI Gateway using your
workspace credentials.

1. **Install `ucode`** (requires [`uv`](https://docs.astral.sh/uv/) and Python 3.12+):

   ```bash
   uv tool install git+https://github.com/databricks/ucode
   ```

2. **Configure it** — this handles OAuth and writes each agent's config for you:

   ```bash
   ucode configure
   ```

   On first run it prompts for your **workspace URL** (the one your admin shared) and
   opens a browser to authenticate. No PAT, no API key, no base URL to paste — `ucode`
   wires the agent to route through the Unity AI Gateway automatically.

3. **Confirm it's connected:**

   ```bash
   ucode status
   ```

   You should see your workspace and the configured agent(s). `ucode` auto-discovers the
   governed models available to you through the Gateway.

> [!TIP]
> `ucode` can launch several agents — `ucode claude`, `ucode codex`, `ucode gemini`,
> `ucode copilot`. Configure just the one you want with
> `ucode configure --agents claude`. All of them route through the Gateway the same way.

---

### **Step 4: Vibe-code the write-back function through the governed agent (15 min)**

Now use your governed AI assistant to build something real: the **`create_service_order`**
Unity Catalog function — the write-back that lets Marc's Supervisor turn a briefing into
an actual service order. You'll *vibe-code* it through a Gateway-routed agent instead of
writing it by hand.

1. Launch a coding agent in a scratch folder (any of the supported ones — Claude Code
   shown here):

   ```bash
   ucode claude
   ```

2. Describe what you need:

   ```
   Write a Databricks Unity Catalog SQL function
   create_service_order(machine_id STRING, fault_code STRING, part_id STRING,
   technician_notes STRING) that returns a STRING order id. It should INSERT a
   row into <catalog>.coffee_maintenance.service_orders with a generated
   order_id like 'SO-12345', current_timestamp(), and status 'pending', then
   return the order_id. Give me the CREATE FUNCTION statement.
   ```

   Every token of that request and response is routed through the **Unity AI Gateway** —
   governed, logged, rate-limited — using your workspace identity, not a personal API key.

3. Iterate with the agent until the function looks right (ask it to add a `COMMENT` so an
   agent knows when to call it, or to handle quoting). Then run the generated
   `CREATE FUNCTION` in a SQL cell against your catalog and test it:

   ```sql
   SELECT <catalog>.coffee_maintenance.create_service_order(
     'CBM-003', 'E-07', 'SIE-EQ9-PUMP-003', 'Vibe-coded in Lab 5'
   ) AS order_id;
   ```

   > [!TIP]
   > **Fallback:** the Lab 0 setup job already registered a working
   > `create_service_order` function. If the vibe-coded version gives you trouble or
   > you're short on time, just use the one from setup — it's ready to go.

4. Now trigger the **PII guardrail**. Ask the agent something with obvious PII in it:

   ```
   Refactor this: customer John Smith, SSN 123-45-6789,
   email john.smith@example.com — store his record in a dict.
   ```

   - With the guardrail in **Sanitize/Mask** mode, the PII is redacted before the model
     ever sees it — the Gateway strips it out in flight.
   - With **Block** mode, the request is rejected outright.

> [!NOTE]
> The developer didn't configure anything. The guardrail lives on the governed service,
> so it protects **every** agent `ucode` routes through it — Claude Code today, Codex or
> Gemini tomorrow. You just built a real write-back function through an AI assistant that
> *cannot* leak PII.

---

### **Step 5: See it in the Coding Agents usage dashboard (5 min)**

1. Quickest check — from your terminal:

   ```bash
   ucode usage
   ```

   This prints your Unity AI Gateway usage summary for the last 7 days: the coding calls
   you just made, tokens, and the model behind them.

2. In the workspace UI, open **Govern → Usage Dashboard → Coding Agents** tab. You'll see
   the calls attributed to you and every other participant — request counts, tokens,
   latency, and which governed model served them.

3. **(Admin, optional)** For a workspace-wide view, query the usage system table in a SQL
   editor:

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

- Use `ucode` to route your own coding agent (Claude Code, Codex, Gemini…) through the
  Unity AI Gateway for your own projects — same governance, your code, no API keys.

> [!TIP]
> Ask your facilitator about follow-up deep-dive sessions on **Agent Bricks**,
> **Lakebase**, and **Databricks Apps**.
