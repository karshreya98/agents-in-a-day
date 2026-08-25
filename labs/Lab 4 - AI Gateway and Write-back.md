# 🔒 Lab 4 — Govern Reusable AI Blocks with the AI Gateway

> 📘 Reference: [**Mosaic AI Gateway** — Databricks docs](https://docs.databricks.com/aws/en/ai-gateway/)

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- See the **AI Gateway** as the control plane for **governed, reusable AI building blocks**.
- Create a governed **model service** — **contextual service policies** (a built-in content
  guardrail + a custom function), **traffic routing / fallback**, **usage + inference
  logging** — and **secure it** with access control in Unity Catalog.
- **Register and secure a governed you.com MCP service** so sensitive actions require
  **approval (ASK)**.
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
**contextual service policies**, traffic management, and monitoring, in one place.

> [!NOTE]
> **Free Edition friendly.** Tasks 1–3 are all done in the **UI** and work on Databricks
> Free Edition. Tasks 4–5 are **bonus** and need a non-Free workspace / admin rights — do
> them if you can, otherwise read along.

---

## Instructions

### **Task 1: Create a governed model service (15 min)**

This is Tim's first reusable block: **one model service every team is allowed to use** —
because it enforces content policies, can't be hammered, and logs everything. Build it up in
three steps.

#### Step 1 — Create the model service (in the AI Gateway)

1. Sidebar → **AI Gateway → Models** tab → click **+ Model** (top right) to open
   **Create Model Service**.

   <img src="./artifacts/Lab%204/lab_4_task_1_a_click_create_model.png" alt="AI Gateway Models tab, + Model button" width="720">

2. A model service is now a **Unity Catalog object** — pick a **Catalog** and **Schema**
   (e.g. `sunny_bay_roastery` / `coffee_maintenance`) and **Name** it `sunny-bay-governed-llm`
   (the name can't be changed after creation).
3. **Provider → Databricks hosted** (pay-per-token, no credentials). Under **Destination**,
   pick an OSS foundation model available on Free Edition — e.g. **Qwen3 Next Instruct**
   (`system.ai.qwen3-next-80b-a3b-instruct`) — then **Create**.

   <img src="./artifacts/Lab%204/lab_4_task_1_b_configure_model_service.png" alt="Create Model Service: catalog, schema, name, provider, destination" width="720">

4. Because it's a UC securable, you can open the model service **two ways** — from
   **AI Gateway → Models** (the gateway view) or from **Catalog Explorer**
   (`sunny_bay_roastery → coffee_maintenance → Services → sunny-bay-governed-llm`, the UC
   view). It's the same object; you'll toggle between the two views through this lab. Either
   way, open its **Permissions** tab and grant your workshop users or group **Can Query** —
   grant / revoke centrally, the same as any UC object. Teams get to *use* it, only Tim
   manages it.

   <img src="./artifacts/Lab%204/lab_4_task_1_c_navigate_uc_permissions_tab.png" alt="Model service opened in Catalog Explorer, Permissions tab" width="720">

#### Step 2 — Configure audit and traffic

Open the model service. Its **Overview** tab shows a **Governance setup** checklist, and the
**Routing** tab controls traffic:

- **Usage tracking** — **on by default**. Every call's token usage is recorded to the
  `system.ai_gateway.usage` system table (per-user, per-model attribution).
- **Inference table** — logs the full request/response payloads to a UC table. This needs a
  workspace with **its own storage**, so you can only enable it if you're **not on default
  storage** — i.e. **not on Free Edition.** On a standard workspace click **Set up**; on Free
  Edition, leave it off.
- **Traffic routing / fallback** — open the **Routing** tab. Your Qwen3 model is the
  **Primary**; click **Add fallback** to add a second model that requests reroute to on
  `429`/`5XX` — resilience without downstream teams doing anything.

<img src="./artifacts/Lab%204/lab_4_task_1_step_2_a_configure_traffic_ai_gateway_tab.png" alt="Routing tab: primary model with Add fallback" width="720">

#### Step 3 — Set up contextual service policies

Open the model service's **Policies** tab → **New policy → Service policy**
(*"control how interactions with this service proceed"*). Add **two** — one out-of-the-box,
one custom — following the
[**AI Gateway moderation tutorial**](https://docs.databricks.com/aws/en/ai-gateway/moderate-tutorial).
Both apply to **All account users** and are scoped to this model service.

**a) Out-of-the-box guardrail.** Name it `block-unsafe-content` and pick the built-in
**Unsafe Content** guardrail (the **Guardrail type** dropdown also offers PII, prompt
injection, and more). It inspects requests and responses and blocks harmful content.

**b) Custom guardrail.** Name it `block-codename`, set **Guardrail type → Custom**, choose
**Custom function**, and point it at the pre-created SQL function
`block_confidential_codename` — a `CASE` expression that **denies** any request mentioning your
confidential project codeword (here, *"project aurora"*). That's the company-specific rule
every team inherits. *(A custom guardrail can also be an **LLM-as-a-judge** instead of a SQL
function.)*

<img src="./artifacts/Lab%204/lab_4_task_1_step_3_add_custom_policy.png" alt="New policy: custom SQL-function guardrail" width="720">

> This is the novel bit: service policies are **contextual**, not static allow/deny lists.
> A custom policy can be a **SQL function** or an **LLM-as-a-judge** that inspects each request
> and response, so the same policy catches a topic however it's phrased.

**Test it in the Playground** (open the model service → **Chat in playground**, or Sidebar →
**Playground** and pick **Qwen3 Next Instruct** — the model your service serves). Ask about the
codename:

> *"Tell me about project aurora"*

The response is refused: **"This request was blocked by the 'block-codename' service policy."**

<img src="./artifacts/Lab%204/lab_4_task_1_step_3_example_service_policy_output_playground.png" alt="Playground: request blocked by the block-codename service policy" width="720">

> [!NOTE]
> Tim configured the service policies **once**. Every agent, app, or Playground session that uses
> this model service now inherits the unsafe-content guardrail, the custom codename rule, and
> the audit log — nobody downstream has to remember to add them.

---

### **Task 2: Build & secure the you.com MCP service (20 min)**

Tim's second reusable block is the **web-search tool**. In Lab 1 you created the metastore
**HTTP connection** `youcom_http` (raw you.com credentials). That connection is *not* something
teams should touch directly — so Tim now wraps it in a **governed MCP service** inside the AI
Gateway, and applies a policy. Same pattern as Task 1, but here the interesting policy is
**ASK**: some actions should pause for a human rather than be hard-allowed or hard-blocked.

#### Step 1 — Register the governed MCP service (on the existing connection)

Turn the raw you.com connection from Lab 1 into a governed, reusable tool. Like the model
service, an MCP service is a **Unity Catalog object**.

1. Sidebar → **AI Gateway → MCPs** → **Create MCP Service**.
2. Pick a **Catalog** and **Schema** (`sunny_bay_roastery` / `coffee_maintenance`) and **Name**
   it `you_web_search_mcp` (the name can't be changed after creation).
3. Under **Connection**, choose **Use existing connection** and select the **you.com connection
   from Lab 1**. Under **Tools**, keep the **`you-search`** tool selected, then **Create MCP
   Service**.

<img src="./artifacts/Lab%204/lab_4_task_2_create_mcp_service_governed.png" alt="Create MCP Service: catalog, schema, name, existing connection, tools" width="720">

4. Open the new MCP service → **Permissions → Grant**, add your workshop users or group, and
   grant **`EXECUTE`**.

> [!WARNING]
> Grant participants **`EXECUTE` on the MCP service only — never `USE CONNECTION`**. As the
> create screen warns, **service policies only govern the MCP service, not the connection** —
> anyone with `USE CONNECTION` can reach you.com directly and bypass your policy. `EXECUTE` is
> all they need to use the tool.
>
> Full reference: [Register an MCP service](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

#### Step 2 — Add a service policy that ASKS

On the MCP service, open the **Policies** tab → **New policy → Service policy**, same as Task 1.
Name it `approve-medical-info`, set **Guardrail type → Custom**, and choose **LLM-as-a-judge**
(a small model reads each request and decides). Set **Action → Ask** — *pause and ask a person
to approve before continuing* — pick an **Evaluator model service** (e.g. `system.ai.gemma-3-12b`),
and give it a plain-language classifier **Prompt**:

> *You are a content classifier. Flag content that contains:*
> - *diseases*
> - *medical terms*
>
> *DO NOT flag:*
> - *financial news*
> - *market research*

<img src="./artifacts/Lab%204/lab_4_task_2_create_governed_mcp_service_policy.png" alt="MCP service policy: Custom LLM-as-a-judge, Action Ask, classifier prompt" width="720">

#### Step 3 — Test the MCP ASK policy in the Playground

Sidebar → **Playground**. Pick **Qwen3 Next Instruct** as the model, and under **Tools**,
**add the `you_web_search_mcp` service**.

| Prompt | What should happen |
|---|---|
| `Tell me about the latest research in Parkinson's disease` | MCP call **triggers an ASK** — a *"Tool requires your approval"* dialog with **Allow / Deny** |
| `What's the latest market outlook for the S&P 500?` | Runs normally — finance/market topics are **not** flagged |

The medical prompt pauses the `you-search` tool for your approval before it runs:

<img src="./artifacts/Lab%204/lab_4_task_2_mcp_playground_ask_example.png" alt="Playground: Tool requires your approval dialog for you-search" width="720">

> [!NOTE]
> If the MCP tool response misbehaves in the Playground (e.g. the tool call hangs or the
> approval doesn't render), run the same prompt from a **notebook** against the model service
> instead — the policy and approval behave the same, and it sidesteps Playground quirks.

> [!NOTE]
> Same governance, two different blocks: the **model** service refuses the blocked topic, and
> the **tool** service pauses for approval on medical topics while letting finance through.
> Any new Sunny Bay use case that reuses these two blocks gets both behaviors automatically.

---

### **Task 3: Monitor in the usage dashboard (5 min)**

Every call you just made is logged — this is Tim's audit trail across all the reusable
blocks.

1. In **AI Gateway**, open the **Govern** menu (top right) → **Usage Dashboard**. You'll see
   request counts, tokens, latency, and per-user attribution across your governed blocks —
   including the requests that were **blocked** by a service policy.

   <img src="./artifacts/Lab%204/lab_4_task_4_see_usage_dashboard.png" alt="AI Gateway Govern menu, Usage Dashboard" width="720">

2. For a workspace-wide view, query the usage system table (the one the model service's
   **Usage tracking** writes to) in a SQL editor:

   ```sql
   SELECT * FROM system.ai_gateway.usage
   ORDER BY 1 DESC
   LIMIT 50;
   ```

> [!NOTE]
> This is the platform team's payoff: every call, from every team, through governed blocks —
> with content policies, approvals, rate limits, and full usage attribution, in one place.

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
   pointed at a governed model service, and code normally — then try a prompt that trips one of
   your policies and watch the guardrail catch it:

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
  hit — the financial guardrail that complements the service policies above.
- Docs: **[Databricks budgets & budget policies](https://docs.databricks.com/aws/en/admin/account-settings/budgets)**.

---

## 🎉 Workshop Complete

**What the Sunny Bay team built today, on Databricks, zero infrastructure to provision:**

| | |
|---|---|
| **Sara** | Built a Genie agent and got machine-health + sales answers from Genie One in plain language, enriched with live web knowledge — no SQL. |
| **Marc** | Built a custom agent, deployed it as a Databricks App with a human-in-the-loop approval gate, gave it durable memory on Lakebase, and had experts review it through MLflow. |
| **Tim (platform IT)** | Stood up **governed, reusable AI blocks** — a policy-governed, traffic-routed, logged model service and an approval-gated web-search tool — so every *next* Sunny Bay use case inherits governance by default. |

**What you take home:**

- The Genie agents and the custom agent — point them at your own data next week.
- The **AI Gateway blocks pattern** — govern models and tools once, reuse everywhere, on
  *your* terms.
- *(If you do the deep dive)* the MLflow trace + Review App loop — how to harden any agent
  with expert feedback.

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
