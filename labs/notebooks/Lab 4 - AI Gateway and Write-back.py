# Databricks notebook source
# MAGIC %md
# MAGIC # 🔒 Lab 4 — Govern Reusable AI Blocks with the AI Gateway
# MAGIC
# MAGIC **Persona: Tim (Platform IT)** &nbsp;·&nbsp; **AI Gateway · service policies · MCP · Playground**
# MAGIC
# MAGIC Stand up governed, reusable AI building blocks — a policy-governed model service and an approval-gated
# MAGIC web-search tool — so every next Sunny Bay use case inherits governance by default.
# MAGIC
# MAGIC 📘 Reference: [**Mosaic AI Gateway** — Databricks docs](https://docs.databricks.com/aws/en/ai-gateway/)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Learning Objectives
# MAGIC
# MAGIC By the end of this lab, you will be able to:
# MAGIC
# MAGIC - See the **AI Gateway** as the control plane for **governed, reusable AI building blocks**.
# MAGIC - Create a governed **model service** — **contextual service policies** (a built-in content guardrail + a custom function), **traffic routing / fallback**, **usage + inference logging** — and **secure it** with access control in Unity Catalog.
# MAGIC - **Register and secure a governed you.com MCP service** so sensitive actions require **approval (ASK)**.
# MAGIC - **Test both blocks in the AI Playground.**
# MAGIC - **Monitor** all of it in the **usage dashboard**.
# MAGIC - *(Bonus)* Route a coding agent through the Gateway with `ucode`; set spend **budgets**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Introduction — meet Tim
# MAGIC
# MAGIC Marc's dispatch agent and Sara's Genie lit a fire at Sunny Bay Roastery. Now half the company wants an
# MAGIC agent — support wants a returns bot, finance wants an invoice reader, marketing wants a campaign helper.
# MAGIC
# MAGIC You're **Tim, head of platform IT**. You *want* to say yes — but not if it means ten teams each pasting
# MAGIC their own model keys into random tools, with no PII protection, no limits, and no audit trail. So you do
# MAGIC what a platform team does: you hand them **governed, reusable building blocks**. One **safe model
# MAGIC endpoint** and one **safe web-search tool** that *every* new use case reuses — with guardrails, rate
# MAGIC limits, approvals, and logging built in, so each new agent inherits governance for free.
# MAGIC
# MAGIC The **AI Gateway** is how you build those blocks. It's Databricks' governance layer for the runtime
# MAGIC interactions between models, agents, MCP servers, and tools — access control, **contextual service
# MAGIC policies**, traffic management, and monitoring, in one place.
# MAGIC
# MAGIC > 📝 &nbsp;**Free Edition friendly.** Tasks 1–3 are all done in the **UI** and work on Databricks Free
# MAGIC > Edition. Tasks 4–5 are **bonus** and need a non-Free workspace / admin rights — do them if you can,
# MAGIC > otherwise read along.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 1: Create a governed model service
# MAGIC
# MAGIC This is Tim's first reusable block: **one model service every team is allowed to use** — because it
# MAGIC enforces content policies, can't be hammered, and logs everything. Build it up in three steps.
# MAGIC
# MAGIC #### Step 1 — Create the model service (in the AI Gateway)
# MAGIC
# MAGIC **1.** Sidebar → **AI Gateway → Models** tab → click **+ Model** (top right) to open **Create Model
# MAGIC Service**.

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_1_a_click_create_model.png" width="680" style="border-radius:8px" alt="AI Gateway Models tab, + Model button">

# COMMAND ----------

# MAGIC %md
# MAGIC **2.** A model service is now a **Unity Catalog object** — pick a **Catalog** and **Schema** (e.g.
# MAGIC `sunny_bay_roastery` / `coffee_maintenance`) and **Name** it `sunny-bay-governed-llm` (the name can't be
# MAGIC changed after creation).
# MAGIC
# MAGIC **3.** **Provider → Databricks hosted** (pay-per-token, no credentials). Under **Destination**, pick an
# MAGIC OSS foundation model available on Free Edition — e.g. **Qwen3 Next Instruct**
# MAGIC (`system.ai.qwen3-next-80b-a3b-instruct`) — then **Create**.

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_1_b_configure_model_service.png" width="680" style="border-radius:8px" alt="Create Model Service: catalog, schema, name, provider, destination">

# COMMAND ----------

# MAGIC %md
# MAGIC **4.** Because it's a UC securable, you can open the model service **two ways** — from **AI Gateway →
# MAGIC Models** (the gateway view) or from **Catalog Explorer** (`sunny_bay_roastery → coffee_maintenance →
# MAGIC Services → sunny-bay-governed-llm`, the UC view). It's the same object; you'll toggle between the two
# MAGIC views through this lab. Either way, open its **Permissions** tab and grant your workshop users or group
# MAGIC **Can Query** — grant / revoke centrally, the same as any UC object. Teams get to *use* it, only Tim
# MAGIC manages it.

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_1_c_navigate_uc_permissions_tab.png" width="680" style="border-radius:8px" alt="Model service opened in Catalog Explorer, Permissions tab">

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 — Configure audit and traffic
# MAGIC
# MAGIC Open the model service. Its **Overview** tab shows a **Governance setup** checklist, and the
# MAGIC **Routing** tab controls traffic:
# MAGIC
# MAGIC - **Usage tracking** — **on by default**. Every call's token usage is recorded to the `system.ai_gateway.usage` system table (per-user, per-model attribution).
# MAGIC - **Inference table** — logs the full request/response payloads to a UC table. This needs a workspace with **its own storage**, so you can only enable it if you're **not on default storage** — i.e. **not on Free Edition.** On a standard workspace click **Set up**; on Free Edition, leave it off.
# MAGIC - **Traffic routing / fallback** — open the **Routing** tab. Your Qwen3 model is the **Primary**; click **Add fallback** to add a second model that requests reroute to on `429`/`5XX` — resilience without downstream teams doing anything.

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_1_step_2_a_configure_traffic_ai_gateway_tab.png" width="680" style="border-radius:8px" alt="Routing tab: primary model with Add fallback">

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 — Set up contextual service policies
# MAGIC
# MAGIC Open the model service's **Policies** tab → **New policy → Service policy** (*"control how interactions
# MAGIC with this service proceed"*). Add **two** — one out-of-the-box, one custom — following the
# MAGIC [**AI Gateway moderation tutorial**](https://docs.databricks.com/aws/en/ai-gateway/moderate-tutorial).
# MAGIC Both apply to **All account users** and are scoped to this model service.
# MAGIC
# MAGIC **a) Out-of-the-box guardrail.** Name it `block-unsafe-content` and pick the built-in **Unsafe Content**
# MAGIC guardrail (the **Guardrail type** dropdown also offers PII, prompt injection, and more). It inspects
# MAGIC requests and responses and blocks harmful content.
# MAGIC
# MAGIC **b) Custom guardrail.** Name it `block-codename`, set **Guardrail type → Custom**, choose **Custom
# MAGIC function**, and point it at the pre-created SQL function `block_confidential_codename` — a `CASE`
# MAGIC expression that **denies** any request mentioning your confidential project codeword (here, *"project
# MAGIC aurora"*). That's the company-specific rule every team inherits. *(A custom guardrail can also be an
# MAGIC **LLM-as-a-judge** instead of a SQL function.)*

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_1_step_3_add_custom_policy.png" width="680" style="border-radius:8px" alt="New policy: custom SQL-function guardrail">

# COMMAND ----------

# MAGIC %md
# MAGIC > This is the novel bit: service policies are **contextual**, not static allow/deny lists.
# MAGIC > A custom policy can be a **SQL function** or an **LLM-as-a-judge** that inspects each request
# MAGIC > and response, so the same policy catches a topic however it's phrased.
# MAGIC
# MAGIC **Test it in the Playground** (open the model service → **Chat in playground**, or Sidebar →
# MAGIC **Playground** and pick **Qwen3 Next Instruct** — the model your service serves). Ask about the
# MAGIC codename:
# MAGIC ```
# MAGIC Tell me about project aurora
# MAGIC ```
# MAGIC The response is refused: **"This request was blocked by the 'block-codename' service policy."**

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_1_step_3_example_service_policy_output_playground.png" width="680" style="border-radius:8px" alt="Playground: request blocked by the block-codename service policy">

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 &nbsp;**Note** — Tim configured the service policies **once**. Every agent, app, or Playground session
# MAGIC > that uses this model service now inherits the unsafe-content guardrail, the custom codename rule, and
# MAGIC > the audit log — nobody downstream has to remember to add them.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 2: Build & secure the you.com MCP service
# MAGIC
# MAGIC Tim's second reusable block is the **web-search tool**. In Lab 1 you created the metastore **HTTP
# MAGIC connection** `youcom_http` (raw you.com credentials). That connection is *not* something teams should
# MAGIC touch directly — so Tim now wraps it in a **governed MCP service** inside the AI Gateway, and applies a
# MAGIC policy. Same pattern as Task 1, but here the interesting policy is **ASK**: some actions should pause
# MAGIC for a human rather than be hard-allowed or hard-blocked.
# MAGIC
# MAGIC #### Step 1 — Register the governed MCP service (on the existing connection)
# MAGIC
# MAGIC Turn the raw you.com connection from Lab 1 into a governed, reusable tool. Like the model service, an
# MAGIC MCP service is a **Unity Catalog object**.
# MAGIC
# MAGIC **1.** Sidebar → **AI Gateway → MCPs** → **Create MCP Service**.
# MAGIC
# MAGIC **2.** Pick a **Catalog** and **Schema** (`sunny_bay_roastery` / `coffee_maintenance`) and **Name** it
# MAGIC `you_web_search_mcp` (the name can't be changed after creation).
# MAGIC
# MAGIC **3.** Under **Connection**, choose **Use existing connection** and select the **you.com connection from
# MAGIC Lab 1**. Under **Tools**, keep the **`you-search`** tool selected, then **Create MCP Service**.

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_2_create_mcp_service_governed.png" width="680" style="border-radius:8px" alt="Create MCP Service: catalog, schema, name, existing connection, tools">

# COMMAND ----------

# MAGIC %md
# MAGIC **4.** Open the new MCP service → **Permissions → Grant**, add your workshop users or group, and
# MAGIC grant **`EXECUTE`**.
# MAGIC
# MAGIC > ⚠️ &nbsp;**Warning** — Grant participants **`EXECUTE` on the MCP service only — never `USE CONNECTION`**.
# MAGIC > As the create screen warns, **service policies only govern the MCP service, not the connection** —
# MAGIC > anyone with `USE CONNECTION` can reach you.com directly and bypass your policy. `EXECUTE` is
# MAGIC > all they need to use the tool.
# MAGIC >
# MAGIC > Full reference: [Register an MCP service](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 — Add a service policy that ASKS
# MAGIC
# MAGIC On the MCP service, open the **Policies** tab → **New policy → Service policy**, same as Task 1.
# MAGIC Name it `approve-medical-info`, set **Guardrail type → Custom**, and choose **LLM-as-a-judge**
# MAGIC (a small model reads each request and decides). Set **Action → Ask** — *pause and ask a person
# MAGIC to approve before continuing* — pick an **Evaluator model service** (e.g. `system.ai.gemma-3-12b`),
# MAGIC and give it a plain-language classifier **Prompt**:
# MAGIC
# MAGIC > *You are a content classifier. Flag content that contains:*
# MAGIC > - *diseases*
# MAGIC > - *medical terms*
# MAGIC >
# MAGIC > *DO NOT flag:*
# MAGIC > - *financial news*
# MAGIC > - *market research*

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_2_create_governed_mcp_service_policy.png" width="680" style="border-radius:8px" alt="MCP service policy: Custom LLM-as-a-judge, Action Ask, classifier prompt">

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 — Test the MCP ASK policy in the Playground
# MAGIC
# MAGIC Sidebar → **Playground**. Pick **Qwen3 Next Instruct** as the model, and under **Tools**,
# MAGIC **add the `you_web_search_mcp` service**.
# MAGIC
# MAGIC | Prompt | What should happen |
# MAGIC |---|---|
# MAGIC | `Tell me about the latest research in Parkinson's disease` | MCP call **triggers an ASK** — a *"Tool requires your approval"* dialog with **Allow / Deny** |
# MAGIC | `What's the latest market outlook for the S&P 500?` | Runs normally — finance/market topics are **not** flagged |
# MAGIC
# MAGIC The medical prompt pauses the `you-search` tool for your approval before it runs:

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_2_mcp_playground_ask_example.png" width="680" style="border-radius:8px" alt="Playground: Tool requires your approval dialog for you-search">

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 &nbsp;**Note** — If the MCP tool response misbehaves in the Playground (e.g. the tool call hangs or
# MAGIC > the approval doesn't render), run the same prompt from a **notebook** against the model service
# MAGIC > instead — the policy and approval behave the same, and it sidesteps Playground quirks.
# MAGIC
# MAGIC > 📝 &nbsp;**Note** — Same governance, two different blocks: the **model** service refuses the blocked topic,
# MAGIC > and the **tool** service pauses for approval on medical topics while letting finance through.
# MAGIC > Any new Sunny Bay use case that reuses these two blocks gets both behaviors automatically.

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:900px">
# MAGIC   <div style="text-align:center;margin:2px 0 18px">
# MAGIC     <div style="font:700 22px system-ui;color:#1f2937">Same governance, two reusable blocks</div>
# MAGIC     <div style="font:600 15px system-ui;color:#B45309;margin-top:2px">Any new Sunny Bay use case that reuses these gets both behaviours automatically</div>
# MAGIC   </div>
# MAGIC   <div style="display:flex;flex-wrap:wrap;gap:16px">
# MAGIC     <div style="flex:1;min-width:280px;border:1px solid #E5E7EB;border-top:4px solid #B22B22;border-radius:14px;padding:18px;background:#fff">
# MAGIC       <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
# MAGIC         <div style="width:40px;height:40px;border-radius:10px;background:#FBEDEC;display:flex;align-items:center;justify-content:center;font-size:20px">🛡️</div>
# MAGIC         <div><div style="font:700 18px system-ui;color:#334155">Model service</div><div style="font-size:13px;color:#64748b">sunny-bay-governed-llm</div></div>
# MAGIC       </div>
# MAGIC       <div style="display:flex;gap:10px;background:#FBEDEC;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#B22B22;font-weight:800">✕</span><div style="font-size:13.5px;color:#3a4250"><b>Refuses</b> the blocked topic — "project aurora" is denied by the custom policy</div></div>
# MAGIC       <div style="display:flex;gap:10px;background:#F8FAFC;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div style="font-size:13.5px;color:#3a4250">Unsafe-content guardrail, traffic fallback, and usage logging — all inherited</div></div>
# MAGIC     </div>
# MAGIC     <div style="flex:1;min-width:280px;border:1px solid #EAD9BE;border-top:4px solid #C77D2A;border-radius:14px;padding:18px;background:#fff">
# MAGIC       <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
# MAGIC         <div style="width:40px;height:40px;border-radius:10px;background:#FBF4E9;display:flex;align-items:center;justify-content:center;font-size:20px">🔎</div>
# MAGIC         <div><div style="font:700 18px system-ui;color:#B45309">MCP tool</div><div style="font-size:13px;color:#8a6a3c">you_web_search_mcp</div></div>
# MAGIC       </div>
# MAGIC       <div style="display:flex;gap:10px;background:#FBF4E9;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#C77D2A;font-weight:800">!</span><div style="font-size:13.5px;color:#3a4250"><b>Pauses for approval</b> on medical topics (ASK) — Allow / Deny before it runs</div></div>
# MAGIC       <div style="display:flex;gap:10px;background:#F0FAF4;border-radius:9px;padding:10px 12px;margin-top:8px"><span style="color:#2F9E68;font-weight:800">✓</span><div style="font-size:13.5px;color:#3a4250">Lets finance/market topics through — same tool, contextual policy</div></div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 3: Monitor in the usage dashboard
# MAGIC
# MAGIC Every call you just made is logged — this is Tim's audit trail across all the reusable
# MAGIC blocks.
# MAGIC
# MAGIC **1.** In **AI Gateway**, open the **Govern** menu (top right) → **Usage Dashboard**. You'll see
# MAGIC request counts, tokens, latency, and per-user attribution across your governed blocks —
# MAGIC including the requests that were **blocked** by a service policy.

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="../artifacts/Lab%204/lab_4_task_4_see_usage_dashboard.png" width="680" style="border-radius:8px" alt="AI Gateway Govern menu, Usage Dashboard">

# COMMAND ----------

# MAGIC %md
# MAGIC **2.** For a workspace-wide view, query the usage system table (the one the model service's
# MAGIC **Usage tracking** writes to) in a SQL editor:

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM system.ai_gateway.usage
# MAGIC ORDER BY 1 DESC
# MAGIC LIMIT 50;

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 &nbsp;**Note** — This is the platform team's payoff: every call, from every team, through governed
# MAGIC > blocks — with content policies, approvals, rate limits, and full usage attribution, in one place.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 4: *(Bonus — non-Free Edition)* Govern a coding agent with `ucode`
# MAGIC
# MAGIC > ⚠️ &nbsp;**Skip on Free Edition.** `ucode` routes coding agents through governed model services,
# MAGIC > but the models available on Free Edition can't be driven by a coding harness. Do this on a
# MAGIC > standard workspace only.
# MAGIC
# MAGIC The same governed endpoint can back your developers' **AI coding assistants**, with no API
# MAGIC keys and full audit — so "vibe coding" happens through *your* models and *your* guardrails.
# MAGIC
# MAGIC **1.** Install `ucode` (Databricks' Unity AI Gateway launcher):
# MAGIC ```bash
# MAGIC uv tool install git+https://github.com/databricks/ucode
# MAGIC ```
# MAGIC
# MAGIC **2.** **Use the coding harness you already have** (Claude Code, Cursor, etc.) — or, if you don't
# MAGIC have one, install **opencode** (free):
# MAGIC ```bash
# MAGIC curl -fsSL https://opencode.ai/install | bash   # only if you need a harness
# MAGIC ```
# MAGIC
# MAGIC **3.** Configure and connect (OAuth, no API keys), then launch your harness through the Gateway
# MAGIC pointed at a governed model service, and code normally — then try a prompt that trips one of
# MAGIC your policies and watch the guardrail catch it:
# MAGIC ```bash
# MAGIC ucode configure --agents <your-harness>   # e.g. opencode
# MAGIC ucode status
# MAGIC ucode <your-harness> --model system.ai.<model>
# MAGIC ```
# MAGIC
# MAGIC **4.** See the calls under **Govern → Usage Dashboard → Coding Agents**, or run `ucode usage`.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Task 5: *(Bonus — admin)* Set a spending budget
# MAGIC
# MAGIC Governed blocks should also have a **budget**. If you have admin access, set a spend budget
# MAGIC so AI usage can't surprise finance; if not, read how it works.
# MAGIC
# MAGIC - **Budgets** let you track and cap AI/compute spend and alert or act when a threshold is hit — the financial guardrail that complements the service policies above.
# MAGIC - Docs: **[Databricks budgets & budget policies](https://docs.databricks.com/aws/en/admin/account-settings/budgets)**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎉 Workshop Complete
# MAGIC
# MAGIC **What the Sunny Bay team built today, on Databricks, zero infrastructure to provision:**

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;flex-wrap:wrap;gap:14px;max-width:940px">
# MAGIC   <div style="flex:1;min-width:250px;border:1px solid #E3D6C2;border-top:4px solid #C77D2A;border-radius:14px;padding:18px;background:#fff">
# MAGIC     <div style="font:700 18px system-ui;color:#B45309;margin-bottom:6px">🗣️ Sara</div>
# MAGIC     <div style="font-size:13.5px;line-height:1.5;color:#3a4250">Built a Genie agent and got machine-health + sales answers from Genie One in plain language, enriched with live web knowledge — no SQL.</div>
# MAGIC   </div>
# MAGIC   <div style="flex:1;min-width:250px;border:1px solid #E3D6C2;border-top:4px solid #7A4BC2;border-radius:14px;padding:18px;background:#fff">
# MAGIC     <div style="font:700 18px system-ui;color:#7A4BC2;margin-bottom:6px">🤖 Marc</div>
# MAGIC     <div style="font-size:13.5px;line-height:1.5;color:#3a4250">Built a custom agent, deployed it as a Databricks App with a human-in-the-loop approval gate, gave it durable memory on Lakebase, and had experts review it through MLflow.</div>
# MAGIC   </div>
# MAGIC   <div style="flex:1;min-width:250px;border:1px solid #CBEAD8;border-top:4px solid #2F9E68;border-radius:14px;padding:18px;background:#fff">
# MAGIC     <div style="font:700 18px system-ui;color:#2F7A54;margin-bottom:6px">🔒 Tim (platform IT)</div>
# MAGIC     <div style="font-size:13.5px;line-height:1.5;color:#3a4250">Stood up governed, reusable AI blocks — a policy-governed, traffic-routed, logged model service and an approval-gated web-search tool — so every next use case inherits governance by default.</div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC **What you take home:**
# MAGIC
# MAGIC - The Genie agents and the custom agent — point them at your own data next week.
# MAGIC - The **AI Gateway blocks pattern** — govern models and tools once, reuse everywhere, on
# MAGIC   *your* terms.
# MAGIC - *(If you do the deep dive)* the MLflow trace + Review App loop — how to harden any agent
# MAGIC   with expert feedback.

# COMMAND ----------

# MAGIC %md
# MAGIC ### What Happens Next?
# MAGIC
# MAGIC - **Go deeper on observability & feedback** → **[Deep Dive: Observability & Feedback](./Deep%20Dives/Observability%20and%20Feedback.md)**
# MAGIC   — see *inside* Marc's agent with MLflow traces, add an LLM-as-a-judge scorer, and collect
# MAGIC   human feedback through a Review App.
# MAGIC - Build the *next* Sunny Bay use case (a returns bot, an invoice reader) on top of the two
# MAGIC   governed blocks you just created — it inherits the guardrails automatically.
# MAGIC - Drop a new PDF into `/Volumes/<catalog>/coffee_maintenance/fault_reports/` and watch it
# MAGIC   flow into `fault_reports_structured` via the Lab 0 Lakeflow pipeline.
# MAGIC
# MAGIC > 💡 &nbsp;**Tip** — Ask your facilitator about follow-up deep-dive sessions on **Agent Bricks**,
# MAGIC > **Lakebase**, and **Databricks Apps**.
