# 🔒 Lab 4 — Govern Reusable AI Blocks with the AI Gateway

> 📘 Reference: [**Mosaic AI Gateway** — Databricks docs](https://docs.databricks.com/aws/en/ai-gateway/)

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- See the **AI Gateway** as the control plane for **governed, reusable AI building blocks**.
- Create a governed **model serving endpoint** — **PII blocking** + a **custom guardrail**,
  **traffic routing / fallback**, **usage + inference logging** — and **secure it** with
  access control in Unity Catalog.
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

### **Task 1: Create a governed model endpoint (15 min)**

This is Tim's first reusable block: **one model endpoint every team is allowed to use** —
because it can't leak PII, can't be hammered, and logs everything. Build it up in three steps.

#### Step 1 — Create the endpoint and set access control

1. Sidebar → **Serving → Create serving endpoint**. Name it `sunny-bay-governed-llm` and
   point it at an OSS foundation model available on Free Edition — e.g.
   **`databricks-qwen3-next-80b-a3b-instruct`** (Qwen3 Instruct). Create it.
2. Open the endpoint's **Permissions** tab and grant your workshop users or a group
   **Can Query**. That's the point of a reusable block: teams get to *use* it, only Tim manages it.
3. This endpoint is a **Unity Catalog securable** — open it in **Catalog (Unity Catalog)** to
   see the same grants there, and how you **grant / revoke** `Can Query` / `Can Manage`
   centrally. Governance on the endpoint = governance in UC.

#### Step 2 — Configure audit and traffic

Open the endpoint's **AI Gateway** / **Edit AI Gateway** panel:

- **Usage tracking** — **on by default**. Every call is logged to `system.serving.endpoint_usage`
  (request counts, tokens, latency, per-user attribution).
- **Inference tables** — logs the full request/response payloads to a UC table. This needs a
  workspace with **its own storage**, so you can only enable it if you're **not on default
  storage** — i.e. **not on Free Edition.** On a standard workspace, turn it on; on Free
  Edition, leave it off.
- **Traffic routing / fallback.** In **Served entities**, add a **second model** and configure
  it as a **fallback** so requests reroute to it on `429`/`5XX`. Keep your primary at 100% and
  let the fallback catch overflow/errors — resilience without downstream teams doing anything.

#### Step 3 — Set up service policies (guardrails)

On the same AI Gateway panel, add **two** guardrails — one out-of-the-box, one custom —
following the [**Configure AI guardrails** tutorial](https://docs.databricks.com/aws/en/ai-gateway/moderate-tutorial):

- **Out-of-the-box → PII detection → `Block`.** Any request or response containing PII (SSNs,
  emails, credit cards, names, addresses) is **rejected**. *(`Mask` redacts instead of
  blocking — for this lab use `Block` so it's obvious.)*
- **Custom → Invalid keywords / Safety.** Add a company-specific rule — e.g. block a
  competitor name or a project codeword — the "custom" guardrail every team inherits.

**Test it in the Playground** (Serving → your endpoint → **Use → Playground**, or Sidebar →
**Playground** with this endpoint selected):

| Prompt | What should happen |
|---|---|
| `My SSN is 123-45-6789, add up the digits for me` | **Blocked** by the PII guardrail — never reaches the model |
| a prompt containing your **custom blocked keyword** | **Blocked** by your custom guardrail |
| any normal question | Answers as usual |

> [!NOTE]
> Tim configured the guardrails **once**. Every agent, app, or Playground session that uses
> this endpoint now inherits PII blocking, the custom rule, and the audit log — nobody
> downstream has to remember to add them.

---

### **Task 2: Secure the you.com MCP connection (15 min)**

Tim's second reusable block is the **web-search tool** (the you.com **MCP** connection you
registered in Lab 1). A tool that reaches the open web needs governing too — same pattern as
Task 1, but here the interesting policy is **ASK**: some actions should pause for a human
rather than be hard-allowed or hard-blocked.

#### Step 1 — Find the connection and set access control

1. Sidebar → **AI Gateway → MCPs** (or **Govern → AI Gateway**) and open the **you.com** MCP
   connection.
2. Grant your workshop users or group access — same as the model endpoint. A governed,
   reusable tool.

#### Step 2 — Set service policies (a custom ASK policy)

Add service policies to the connection, same as Task 1. The custom one is an **ASK** policy: a
human must **approve** before the tool runs. Scope it to **medical / health topics** so it
flags **diseases and medical information**, but **not** finance or market questions.

> Write the policy's "Ask" intent in plain language, e.g.:
> *"Ask for human approval when the request is about medical conditions, diseases, symptoms,
> or treatments. Do not flag questions about finance, markets, stocks, or business."*

#### Step 3 — Test both blocks in the Playground

Sidebar → **Playground**. Select your **`sunny-bay-governed-llm`** endpoint from Task 1, and
**add the you.com MCP** as a tool.

| Prompt | What should happen | Which block |
|---|---|---|
| `My SSN is 123-45-6789, count the sum of the digits` | **Blocked** by the PII guardrail — the request never reaches the model | Task 1 (PII) |
| `Tell me about the latest research in Parkinson's disease` | MCP call **triggers an ASK** — approve before the web search runs | Task 2 (medical → ASK) |
| `What's the latest market outlook for the S&P 500?` | Runs normally — finance/market topics are **not** flagged | Task 2 (finance → allow) |

> [!NOTE]
> Same governance, two different blocks: the **model** endpoint refuses to touch PII, and
> the **tool** connection pauses for approval on medical topics while letting finance through.
> Any new Sunny Bay use case that reuses these two blocks gets both behaviors automatically.

---

### **Task 3: Monitor in the usage dashboard (5 min)**

Every call you just made is logged — this is Tim's audit trail across all the reusable
blocks.

1. Open the **AI Gateway → Usage dashboard** (**Govern → AI Gateway → Usage**). You'll see
   request counts, tokens, latency, and per-user attribution across your governed blocks —
   including the requests that were **blocked** by the PII guardrail.

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

1. Install `ucode` (Databricks' Unity AI Gateway launcher):

   ```bash
   uv tool install git+https://github.com/databricks/ucode
   ```

2. **Use the coding harness you already have** (Claude Code, Cursor, etc.) — or, if you don't
   have one, install **opencode** (free):

   ```bash
   curl -fsSL https://opencode.ai/install | bash   # only if you need a harness
   ```

3. Configure and connect (OAuth, no API keys), then launch your harness through the Gateway
   pointed at a governed model service, and code normally — then try a PII prompt and watch the
   guardrail catch it:

   ```bash
   ucode configure --agents <your-harness>   # e.g. opencode
   ucode status
   ucode <your-harness> --model system.ai.<model>
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
| **Tim (platform IT)** | Stood up **governed, reusable AI blocks** — a PII-safe, traffic-routed, logged model endpoint and an approval-gated web-search tool — so every *next* Sunny Bay use case inherits governance by default. |

**What you take home:**

- The Genie agents and the custom agent — point them at your own data next week.
- The MLflow trace + Review App loop — the way to harden any agent with expert feedback.
- The **AI Gateway blocks pattern** — govern models and tools once, reuse everywhere, on
  *your* terms.

---

## What Happens Next?

- **Go deeper on observability & feedback** → **[Deep Dive: Observability & Feedback](./Deep%20Dives/Observability%20and%20Feedback.md)**
  — see *inside* Marc's agent with MLflow traces, add an LLM-as-a-judge scorer, and collect
  human feedback through a Review App.
- Build the *next* Sunny Bay use case (a returns bot, an invoice reader) on top of the two
  governed blocks you just created — it inherits the guardrails automatically.
- Drop a new PDF into `/Volumes/<catalog>/coffee_maintenance/fault_reports/` and watch it
  flow into `fault_reports_structured` via the Lab 0 Lakeflow pipeline.

> [!TIP]
> Ask your facilitator about follow-up deep-dive sessions on **Agent Bricks**,
> **Lakebase**, and **Databricks Apps**.
