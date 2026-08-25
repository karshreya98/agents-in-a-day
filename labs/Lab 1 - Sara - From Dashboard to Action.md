# 🗣️ Lab 1 - Sara - From Dashboard to Action

## 🎯 Learning Objectives

By the end of Lab 1, you will be able to:

- Build a **Genie agent** (formerly *Genie space*) over the Sunny Bay maintenance data.
- Use **Genie One** as a business-user interface, driven by that Genie agent.
- Connect an external **MCP tool** (you.com) to enrich Genie One conversations with live web knowledge.
- Package a repeated question as a reusable **skill** and put it on a **schedule**, so Genie One briefs Sara automatically.

## Key concepts

| Term | What it means here |
|---|---|
| **Genie agent** | A governed natural-language interface over specific Unity Catalog tables (menus may still say *Genie space* — same thing). You build the Maintenance one; Sales is pre-built. |
| **Genie One** | The chat front door. It **routes** each question to the Genie agent whose description matches — you don't pick a space first. |
| **MCP** | *Model Context Protocol* — a standard way to plug an external tool (here, you.com web search) into Genie One or the AI Gateway. |
| **Skill** | A saved prompt/capability in Genie One so Sara doesn't re-type the same question. You can **schedule** a skill to run on a cadence. |

## Introduction

Sara is the Mission location manager at Sunny Bay Roastery. Day to day she doesn't
write SQL or dig through tables — she just wants answers. She gets them through
**Genie One**, the conversational front door to Databricks. Behind Genie One sits a
**Genie agent**: a governed, natural-language interface to a set of Unity Catalog tables.

> [!NOTE]
> **Naming:** Genie agents were previously called **Genie spaces** — you'll still see
> "space" in some menus and URLs. They're the same thing; this lab uses **Genie agent**.

In this lab you'll wear two hats: first you set up the Genie agent (a quick,
one-time build), then you step into Sara's shoes and just ask questions.

You build **one** Genie agent here — a **Maintenance Genie** (the one Sara, and later
Marc's custom agent in Lab 3, needs for machine faults) — over the maintenance tables the
setup job seeded. The setup job also **pre-built a Sales Genie** (Sunny Bay coffee sales
by store), so you end up with two agents in the workspace and talk to *both* through
Genie One, which routes each question to the right agent.

This lab is **facilitator-led with participant follow-along**. No code to write. Just one
Genie agent and a few conversations.

---

## Instructions

### **Step 1: Build the Maintenance Genie agent (10 min)**

The Lab 0 setup job already created the core maintenance tables. Now you'll put a Genie
agent in front of them.

1. In the workspace left sidebar, click **Genie**.

2. Click **New** (or **+ New Genie space**).

3. When prompted for data, add these three tables from your catalog's
   `coffee_maintenance` schema:

   ```
   <catalog>.coffee_maintenance.machines
   <catalog>.coffee_maintenance.fault_events
   <catalog>.coffee_maintenance.service_orders
   ```

   > [!NOTE]
   > Replace `<catalog>` with the catalog name you used in Lab 0 (e.g.
   > `sunny_bay_roastery`).

4. Name the space **`Sunny Bay Maintenance Genie`** and give it a description:

   ```
   Natural-language Q&A over Sunny Bay espresso machine maintenance: machine
   registry, fault event history, and service orders. Use for questions about a
   machine's faults, fault codes, locations, and service history. Covers
   machines CBM-001 to CBM-012, fault codes such as E-07 pressure faults,
   the 12 Sunny Bay locations including Mission District, and open or
   completed service orders.
   ```

   > [!IMPORTANT]
   > **Be generous and specific in this description.** Genie One uses it to decide
   > whether *this* agent is the right one to answer a question. Name the actual
   > entities a user might mention — machine IDs, fault codes, location names,
   > the words "service order" — so questions phrased in the user's own language
   > still match. A thin description is the most common reason Genie One skips an
   > agent (see the callout in Step 3).

5. Click **Save**.

> [!NOTE]
> Right now this agent answers from the structured maintenance tables. In **Lab 2**
> you'll turn the raw PDF fault reports into a `fault_reports_structured` table and add
> it to *this same agent* — so it can also answer about what's written in the reports.

> [!TIP]
> You'll reuse this exact Genie agent in **Lab 3** as one of the tools Marc's custom
> agent composes — building it once here means it's ready when you get there.

> [!NOTE]
> **You already have a second agent — the setup job pre-built a `Sunny Bay Sales Genie`**
> over the governed sales **metric view** (`<catalog>.gold.sm_fact_coffee_sales_genie`),
> exposing measures like gross revenue, profit, and units sold sliced by store, product,
> and date. You don't build it — you'll just talk to it through Genie One in Step 3.

> [!NOTE]
> You now have two Genie agents in the workspace — the maintenance one you just built and
> the pre-built sales one. That's exactly what Genie One needs to demonstrate routing in
> Step 3, and both become tools of Marc's custom agent in Lab 3.

---

### **Step 2: Ask maintenance questions in the Genie agent (5 min)**

1. In the Genie agent you just built, start a conversation and try:

   ```
   Which machines have logged E-07 pressure faults?
   ```

   ```
   Show me the fault event history for the Mission District location
   ```

   ```
   Which machines are due for service?
   ```

2. Click **Show code** beneath any answer to see the SQL Genie generated — no one
   wrote it by hand.

> [!NOTE]
> **A Genie agent has two modes — chat and agent.** Look for the mode selector in the
> conversation box and try the same question in each.
>
> | | **Chat mode** | **Agent mode** |
> |---|---|---|
> | How it answers | One question → one SQL query → one answer | Plans, then takes several steps, and can chain queries before replying |
> | Best for | Quick, direct lookups — *"which machines logged E-07 faults?"* | Broader, multi-part questions — *"which machines need attention this week and why?"* |
> | Speed | Faster | Slower, since it does more work |
> | Verified answers | A trusted asset (a parameterized query your admin blessed) returns a **verified answer** | Reasons more freely across the data |
>
> Same governed tables and same Unity Catalog permissions either way — the difference is
> how much reasoning Genie does before it answers.

> [!TIP]
> Ask *"which machines need attention this week and why?"* in **chat mode**, then again in
> **agent mode**. Chat mode gives you one query's worth of answer; agent mode breaks the
> question down and works through it. That contrast is exactly what you're building at
> scale in Lab 3 — the custom agent runs this kind of planning across *multiple* tools.

> [!NOTE]
> Genie answers from the governed tables only — right now, the machine registry, fault
> events, and service orders. It can't yet read the *fault report PDFs*; that's what
> Lab 2 adds.

---

### **Step 3: Talk to your Genie agents through Genie One (5 min)**

Genie One is the business-user front door. Every Genie agent in the workspace shows
up here as an **agent** — including the **Sunny Bay Maintenance Genie** you just built
*and* the pre-built **Sunny Bay Sales Genie**. Sara doesn't pick a table or an agent; she
just asks, and Genie One routes to the right one.

1. Open the **kebab menu** (the ⋮ / grid "waffle" icon in the top navigation bar) and
   select **Genie One**.

2. Ask Sara's manager questions — a mix of **maintenance** and **sales**. Genie One
   routes each to the right Genie agent:

   **Maintenance** (routes to the Sunny Bay Maintenance Genie you built):

   ```
   Which of my machines should I be worried about this week?
   ```

   ```
   How many unresolved faults does CBM-003 have?
   ```

   **Sales** (routes to the pre-built Sunny Bay Sales Genie):

   ```
   How do sales at the Sunny Bay – Mission store compare to the other stores?
   ```

   ```
   Which store had the highest coffee revenue in 2024?
   ```

3. **Check *what* answered you.** Click the **citation icons** in a response to see the
   knowledge sources Genie One used. You want to see your **Genie agent** named there —
   not just a bare SQL result.

> [!NOTE]
> One conversation, two governed Genie agents — maintenance *and* sales — with no
> switching. Sara configured nothing; she just asks. Unity Catalog governs what each
> agent can see.

> [!IMPORTANT]
> **If the answer came back as a direct query instead of via your Genie agent.**
> This is expected behaviour, not a bug. Genie One resolves a question in this order:
>
> 1. It searches the available **Genie agents** for one relevant to your question.
> 2. If it finds a match, it uses that agent to answer.
> 3. **If it finds no match, it falls back to searching data assets directly** — which
>    is why you sometimes get a raw query result with no agent listed as the source.
>
> So an answer with no agent attribution means step 1 didn't match. Fixes, in order of
> effectiveness:
>
> - **Enrich the agent description** (Step 1, task 4). This is the single biggest lever —
>   it's the text Genie One matches against. Add the machine IDs, fault codes, and
>   location names a user would actually say.
> - **Use vocabulary that only that agent covers.** "How many unresolved *faults* does
>   *CBM-003* have?" matches far more reliably than "how are my machines doing?".
> - **Ask it explicitly:** *"Using the Sunny Bay Maintenance Genie, which machines have
>   logged E-07 faults?"*
> - **Or pick the agent by hand.** If Genie One's chat doesn't route well, click **Ask** in
>   the search bar and select the Genie agent yourself — that bypasses routing entirely and
>   drops you straight into the agent (where you also get the chat/agent mode selector from
>   Step 2).
>
> **Facilitator tip:** this is worth demoing deliberately. Ask a vague question, show the
> unattributed query result, then improve the description and ask again. Watching the
> agent *become* the source teaches why descriptions are routing rules — the same lesson
> Lab 3 builds on when the custom agent picks between its tools.

---

### **Step 4: Connect you.com for live web knowledge (15 min)**

The telemetry tells Sara *what* is happening. It cannot tell her *why*, or what the
manufacturer recommends. An external **MCP service** (you.com), registered in the Unity
AI Gateway, fixes that.

**Step 4a — Get your you.com API key**

1. Open a new browser tab and go to [https://you.com](https://you.com).

2. Click **Sign up** — you can use Google or GitHub. The free tier is sufficient.

3. After signing in, go to [https://you.com/settings/api](https://you.com/settings/api).

4. Click **Create API key** → copy the key (it looks like `yk_...`).

> [!TIP]
> No credit card required. The free plan gives 100 web-search calls/day — more
> than enough for this workshop. You keep this key after the session.

**Step 4b — Check whether the you.com MCP service already exists**

1. In the workspace sidebar, open **AI Gateway** → **MCPs**.

2. Look for a **you.com** MCP service.

   - **It's there** → skip to **Step 4c**. Someone already registered it.
   - **It's not there** → do **Step 4b-1** below to create it yourself.

---

**Step 4b-1 — Register the you.com connection in Unity Catalog**

First create the Unity Catalog **HTTP connection**, then register the MCP service on top of it.

1. Go to **Catalog** → **Connections** → **Create connection**.

2. Select **HTTP** as the connection type.

3. Name it `youcom_http`, set the authentication type to **Bearer token**, paste the key from Step 4a and 
use these settings:

   | Field | Value                     |
   |---|---------------------------|
   | Connection type | HTTP                      |
   | URL | `https://api.you.com:443` |
   | Base path | `/mcp`                    |
   | Is mcp connection | `true`                    |
   | Auth scheme | `bearer`                  |
   | Host | `https://api.you.com`     |
   | Port | `443`                     |


> [!IMPORTANT]
> **Create this connection at the metastore level, not inside a catalog or schema.**
> It is a metastore-scoped object: create it once and every workspace on the metastore
> can use it. Don't repeat it per workspace or per participant.
>
> You need `CREATE CONNECTION` to do this. If the option is greyed out, you don't have
> the privilege — ask your facilitator or a metastore admin to create it.

**Step 4c — Ask enriched questions**

In Genie One, enable the you.com connection you created `Customizations > Connections > Toggle youcom_http`.    
You can now ask questions that combine your governed data with the web:

```
What does Siemens recommend when a repeated E-07 pressure error appears on
their commercial coffee machines?
```

```
Are there any known service bulletins for pressure faults on Nespresso Pro
commercial machines?
```

> [!NOTE]
> Internal maintenance data and live web knowledge in the same conversation. Unity
> Catalog data never moved — the context just got richer.

---

### **Step 5: Turn Sara's weekly check into a skill — and schedule it (optional, 15 min)**

Sara keeps asking the same weekly question: *which machines need attention, and why?*
Genie One lets her stop re-typing it. Two features turn a repeated question into something
durable:

- A **skill** — a custom, reusable capability she creates once and runs any time.
- A **scheduled task** — a question (or skill) Genie One re-runs on a cadence and emails to
  her as a briefing, no prompting required.

Sara wants to send the results of her findings to her maintenance team. Genie One supports managed connections 
with GSuite and MS365. For this Lab, we will use Gmail.  

**Enable the connector click on the `+` sign on the below the text box and enable the connection
with Gmail (credentials will be communicated by the instructor).**

> [!NOTE]
> **Skills and scheduled tasks are personal to you.** A skill you create lives in your own
> Genie One — it isn't shared with the workspace. In the near future, skills will be shareable
> enabling teams to share standard and best practices.

**Step 5a — Create a skill**

In Genie One chat, just describe the capability you want. Genie One writes the skill and
saves it for you:

```
Create a user skill called "maintenance update email drafter".

When the skill is invoked or if you are asked to prepare a maintenance update:

1. Use the Sunny Bay Maintenance Genie to identify relevant machines, recent faults and
   repeated fault codes.

2. Using the Gmail connector, draft an email to maintenance@sunnybailroastery.com:
   - Start with a clear subject line.
   - Summarize the situation in plain business language.
   - Identify affected machines and locations.
   - Explain the operational impact without unnecessary technical jargon.
   - List recommended actions, owners, and urgency.
   - End with a clear request or next step.
```

Genie One creates the skill and saves it to your workspace at
`/Workspace/Users/<your-email>/.assistant/skills/` and accessible on the tab `Customizations > Skill`
where it can be edited or deleted and (soon) shared.

**Step 5b — Execute the skill**

Two ways to run it:

- **Invoke it by hand:** type `/` in the chat input and pick your skill from the list.
- **Let Genie One load it:** just ask a related question. Genie One automatically loads the
  skill when it decides the skill is relevant to your request — you don't have to name it.

You still get **Show code** and the **citation icons** on the answer, exactly as in Steps 2–3.

At the end of the skill execution, a new draft will be written in Gmail.

**Step 5d — Schedule it as a standing briefing**

Now make it run itself. The fastest way is to just ask in chat:

```
Run maintenance update email drafter every Monday at 7am.
```

Or create it deliberately from the sidebar:

1. In the Genie One sidebar, click **Schedules**.
2. Open the dropdown next to **+ Create in chat** and choose **Create manually**.
3. Fill in **Title**, **Instructions** (the question or skill to run), **Connections** (the
   data/agent the task should use — your Maintenance Genie agent, plus you.com for bulletins),
   **Schedule** (e.g. weekly, Monday 07:00), and **Timezone**.
4. Click **Create**. Use **Run now** to fire it immediately and check the output.

When the task runs it **posts the results in a chat thread and emails you the results with a
PDF attachment** — so Sara gets her Monday briefing whether or not she's in Databricks that
morning.

> [!NOTE]
> Manage every scheduled task under **Scheduled tasks** in the sidebar: click one to see its
> past runs, edit it, or delete it. To pull a task into a fresh conversation, **@mention** it
> in chat.

> [!NOTE]
> **Facilitator note:** Skills and scheduled tasks are newer Genie One capabilities. Confirm
> they're enabled in your workshop workspace before the session — some Free Edition workspaces
> may not have them yet. If they're unavailable, demonstrate the *intent* instead: Sara defines
> the weekly machine-health question once, and Genie One runs it for her every Monday morning.

The point stands either way: **Sara defines the *question* once. Genie does the *work* — on
demand and on a schedule.**

Full reference: [Chat in Genie One](https://docs.databricks.com/aws/en/genie-one/chat)
(covers both user skills and scheduled tasks).

---

## Bridge to Marc's Arc

Sara's machine check just flagged **CBM-003: pressure anomaly, repeated E-07 fault
codes**.

She can *see* it. But who decides what to *do* about it — across all 12 locations at once?

That's **Marc**, the operations manager. He runs the 12 location managers (Sara among
them) and has to prioritise: which machines threaten which stores, who to dispatch, and
who to tell. The fault history is already in Unity Catalog — the same Maintenance Genie
Sara queried knows it. The question is whether Marc has something that turns it into a
*decision and an action*.

**Over Labs 2–3 you build that.**

---

## What Happens Next?

You have built a Genie agent, driven it from Genie One as a business user, enriched it with
live web knowledge — and, optionally, packaged Sara's weekly check as a scheduled skill that
briefs her automatically — all on governed data that never left Unity Catalog.

➡️ Continue to **[Lab 2 — Document Intelligence](./Lab%202%20-%20Marc%20-%20Document%20Intelligence.md)**
  to start building Marc's manager analysis.
