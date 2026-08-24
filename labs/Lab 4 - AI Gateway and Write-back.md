# 🔒 Lab 4 — Govern Reusable AI Blocks with the AI Gateway

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- See the **AI Gateway** as the control plane for **governed, reusable AI building blocks**.
- Create a governed **model serving endpoint** — **PII blocking** + a **custom guardrail**,
  **rate limits**, **traffic routing / fallback**, **inference + usage logging** — and
  **secure it** with access control.
- **Secure the you.com MCP connection** so sensitive actions require **approval (ASK)**.
- **Test both blocks in the AI Playground.**
- **Monitor** all of it in the **usage dashboard**.
- *(Bonus)* Route a coding agent through the Gateway with `ucode`; set spend **budgets**.

## Introduction — meet Tim

Marc's dispatch agent and Sara's Genie lit a fire at Sunny Bay Roastery. Now half the
company wants an agent — support wants a returns bot, finance wants an invoice reader,
marketing wants a campaign helper.

You're **Tim, head of platform IT**. You *want* to say yes — but not if it means ten teams
each pasting their own model keys into random tools, with no PII protection, no limits, and
no audit trail. So you do what a platform team does: you hand them **governed, reusable
building blocks**. One **safe model endpoint** and one **safe web-search tool** that *every*
new use case reuses — with guardrails, rate limits, approvals, and logging built in, so each
new agent inherits governance for free.

The **AI Gateway** is how you build those blocks. It's Databricks' governance layer for the
runtime interactions between models, agents, MCP servers, and tools — access control,
guardrails, traffic management, and monitoring, in one place.

> [!NOTE]
> **Free Edition friendly.** Tasks 1–3 are all done in the **UI** and work on Databricks
> Free Edition. Tasks 4–5 are **bonus** and need a non-Free workspace / admin rights — do
> them if you can, otherwise read along.

---

## Instructions

### **Task 1: Create a governed model endpoint (10 min)**

This is Tim's first reusable block: **one model endpoint every team is allowed to use** —
because it can't leak PII, can't be hammered, and logs everything.

1. **Create the endpoint.** Sidebar → **Serving → Create serving endpoint**. Give it a name
   like `sunny-bay-governed-llm` and point it at an OSS foundation model available on Free
   Edition — e.g. **`databricks-qwen3-next-80b-a3b-instruct`** (Qwen3 Instruct). Create it.

2. **Open the endpoint's AI Gateway settings** (the **AI Gateway** / **Edit AI Gateway**
   panel on the endpoint) and configure the block:

   - **Guardrails → PII detection → `Block`.** This is the headline rule: any request or
     response containing PII (SSNs, emails, credit cards, names, addresses) is **rejected**.
     *(`Mask` redacts instead of blocking — for this lab use `Block` so it's obvious.)*
   - **Guardrails → add a custom rule.** Turn on **Safety**, and add an **Invalid keywords**
     guardrail with a term your org wants blocked (e.g. a competitor name or a project
     codeword) — that's your "custom" guardrail: a company-specific rule every team inherits.
   - **Rate limits.** Set an **endpoint** limit and a **per-user default** (e.g. 60 queries
     per minute) so no single use case can starve the others.
   - **Traffic / fallback (routing).** In **Served entities**, keep your model at 100%, and
     *(optional)* add a second model as a **fallback** so requests reroute on `429`/`5XX`.
   - **Usage tracking → on** and **Inference tables → on** so every call is logged and
     auditable (`system.serving.endpoint_usage`).

3. **Secure the block (access control).** On the endpoint's **Permissions**, grant your
   workshop users or a group **Can Query**. That's the point of a reusable block: teams get
   to *use* it, only Tim configures the guardrails.

> [!NOTE]
> Tim configured the guardrails **once**. Every agent, app, or Playground session that uses
> this endpoint now inherits PII blocking, the custom rule, the rate limits, and the audit
> log — nobody downstream has to remember to add them.

---

### **Task 2: Secure the you.com MCP connection, and test both in the Playground (15 min)**

Tim's second reusable block is the **web-search tool** (the you.com **MCP** connection you
registered in Lab 1). A tool that reaches the open web needs a guard too — some actions
should pause for a human.

1. **Find the MCP connection.** Sidebar → **AI Gateway → MCPs** (or **Govern → AI
   Gateway**) and open the **you.com** MCP connection.

2. **Attach a policy that ASKS.** Add a service policy so sensitive calls return **ASK** —
   a human must approve before the tool runs (rather than a hard allow/deny). For this lab,
   scope it to **health / medical** topics, so a Parkinson's query trips the approval.

3. **Grant access.** Grant your workshop group access to the MCP connection, same as the
   model endpoint — a governed, reusable tool.

4. **Test both blocks in the AI Playground.** Sidebar → **Playground**. Select your
   **`sunny-bay-governed-llm`** endpoint from Task 1, and **add the you.com MCP** as a tool.

   | Prompt | What should happen | Which block |
   |---|---|---|
   | `My SSN is 123-45-6789, count the sum of the digits` | **Blocked** by the PII guardrail — the request never reaches the model | Task 1 (PII block) |
   | `Tell me about the latest research in Parkinson's disease` | The MCP call **triggers an ASK** — you're prompted to approve before the web search runs | Task 2 (MCP policy) |

> [!NOTE]
> Same governance, two different blocks: the **model** endpoint refuses to touch PII, and
> the **tool** connection pauses for approval on sensitive actions. Any new Sunny Bay use
> case that reuses these two blocks gets both behaviors automatically.

---

### **Task 3: Monitor in the usage dashboard (5 min)**

Every call you just made is logged — this is Tim's audit trail across all the reusable
blocks.

1. Open **Serving → your endpoint → Usage** (or **Govern → AI Gateway → Usage dashboard**).
   You'll see request counts, tokens, latency, and per-user attribution — including the
   requests that were **blocked** by the PII guardrail.

2. For a workspace-wide view, query the usage system table in a SQL editor:

   ```sql
   SELECT
     date_trunc('hour', request_time) AS hour,
     requester,
     count(*)               AS requests,
     sum(input_token_count) AS input_tokens,
     sum(output_token_count) AS output_tokens
   FROM system.serving.endpoint_usage
   WHERE endpoint_name = 'sunny-bay-governed-llm'
   GROUP BY ALL
   ORDER BY hour DESC
   ```

> [!NOTE]
> This is the platform team's payoff: every call, from every team, through governed blocks —
> with PII protection, approvals, rate limits, and full usage attribution, in one place.

---

### **Task 4: *(Bonus — non-Free Edition)* Govern a coding agent with `ucode`**

> [!IMPORTANT]
> **Skip on Free Edition.** `ucode` routes coding agents through governed model services,
> but the models available on Free Edition can't be driven by a coding harness. Do this on a
> standard workspace only.

The same governed endpoint can back your developers' **AI coding assistants**, with no API
keys and full audit — so "vibe coding" happens through *your* models and *your* guardrails.

1. Install a coding agent and `ucode` (Databricks' Unity AI Gateway launcher):

   ```bash
   curl -fsSL https://opencode.ai/install | bash
   uv tool install git+https://github.com/databricks/ucode
   ```

2. Configure and connect (OAuth, no API keys):

   ```bash
   ucode configure --agents opencode
   ucode status
   ```

3. Launch the agent through the Gateway, pointed at a governed model service, and code
   normally — then try a PII prompt and watch the guardrail catch it:

   ```bash
   ucode opencode --model system.ai.<model>
   ```

4. See the calls under **Govern → Usage Dashboard → Coding Agents**, or run `ucode usage`.

---

### **Task 5: *(Bonus — admin)* Set a spending budget**

Governed blocks should also have a **budget**. If you have admin access, set a spend budget
so AI usage can't surprise finance; if not, read how it works.

- **Budgets** let you track and cap AI/compute spend and alert or act when a threshold is
  hit — the financial guardrail that complements the safety guardrails above.
- Docs: **[Databricks budgets & budget policies](https://docs.databricks.com/aws/en/admin/account-settings/budgets)**.

---

## 🎉 Workshop Complete

**What the Sunny Bay team built today, on Databricks, zero infrastructure to provision:**

| | |
|---|---|
| **Sara** | Built a Genie agent and got machine-health + sales answers from Genie One in plain language, enriched with live web knowledge — no SQL. |
| **Marc** | Built a custom agent, deployed it as a Databricks App with a human-in-the-loop approval gate, gave it durable memory on Lakebase, and had experts review it through MLflow. |
| **Tim (platform IT)** | Stood up **governed, reusable AI blocks** — a PII-safe, rate-limited, logged model endpoint and an approval-gated web-search tool — so every *next* Sunny Bay use case inherits governance by default. |

**What you take home:**

- The Genie agents and the custom agent — point them at your own data next week.
- The MLflow trace + Review App loop — the way to harden any agent with expert feedback.
- The **AI Gateway blocks pattern** — govern models and tools once, reuse everywhere, on
  *your* terms.

---

## What Happens Next?

- Build the *next* Sunny Bay use case (a returns bot, an invoice reader) on top of the two
  governed blocks you just created — it inherits the guardrails automatically.
- Drop a new PDF into `/Volumes/<catalog>/coffee_maintenance/fault_reports/` and watch it
  flow into `fault_reports_structured` via the Lab 0 Lakeflow pipeline.

> [!TIP]
> Ask your facilitator about follow-up deep-dive sessions on **Agent Bricks**,
> **Lakebase**, and **Databricks Apps**.
